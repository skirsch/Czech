import csv
import datetime
import bisect
import os
import pickle
import sys

##################################################
# USAGE
# python buckets.py <src_file.csv> <optional prefix> <optional vax count> <optional fitler flag>
# src_file.csv is the file you want processed, has to be in the format of the NZ data
# prefix - as a prefix to the output files and also for the pickle cache
# vax count - only process people with exactly a certain number of doses
# filter flag - 'FILTER' if you want to filter people who may have skipped a dose
##################################################

# Don't judge me here, these are global because I wrote it just
# to parse a single type of file

# (vax date, dose, batch) tuple sorted by vax date per person
vax_dates = {}

# death date per person
death_dates = {}

# age per person
vax_age = {}

# people in different sets
all_people = set()
vaxxed_people = set()
unvaxxed_people = set()

# all the dates in the data
all_dates = set()


def read_nov9_csv(fname):
    # if we don't have a death date, then we use today for the age
    today = datetime.date.today()
    date_sep_char = None

    with open(fname, 'r') as file:
        reader = csv.reader(file)
        reader.__next__()  # bypass header
        for row in reader:
            # we loop through possible dates and try to
            # determine if - or / is the date separator
            # once we find one, we keep it the same for
            # the whole file
            if date_sep_char is None:
                # we check death, vax, and birth dates for a valid date
                # first one wins
                for test_row in [4, 5, 6]:
                    if '-' in row[test_row]:
                        date_sep_char = '-'
                        break
                    if '/' in row[test_row]:
                        date_sep_char = '/'
                        break
            if date_sep_char is None:
                continue
            # the unique identifer for the person, typically
            # this is the obfuscated MRN or something like that
            pid = row[0]

            # vaccine batch number
            vax_batch = int(row[1])

            # dose number
            vax_dose = int(row[2])

            # vax date
            if len(row[5]) > 0:
                (m, d, y) = row[3].split(date_sep_char)
                vax_date = datetime.date(int(y), int(m), int(d))
                if pid not in vax_dates:
                    vax_dates[pid] = []
                bisect.insort(vax_dates[pid], (vax_date, vax_dose, vax_batch))
                all_dates.add(vax_date)
                vaxxed_people.add(pid)

            # death date
            if len(row[4]) > 0:
                (m, d, y) = row[4].split(date_sep_char)
                death_date = datetime.date(int(y), int(m), int(d))
                if pid in death_dates and death_dates[pid] != death_date:
                    print(f'WARNING: death date for #{pid} is not consistent')
                death_dates[pid] = death_date
                all_dates.add(death_date)
            else:
                # if we don't have a death data, we just use today for
                # computing age below.  We don't store them as a dead person
                death_date = today

            # birth date
            (m, d, y) = row[6].split(date_sep_char)
            birth_date = datetime.date(int(y), int(m), int(d))
            tmp_age = (death_date - birth_date).days // 365
            if pid in vax_age and vax_age[pid] != tmp_age:
                print(f'WARNING: age for #{pid} is not consistent')
            vax_age[pid] = tmp_age

            all_people.add(pid)


#######################################
#######################################
#######################################


def make_buckets(n_vax=None):
    # This is a pretty inefficient loop, if I did this in a productiong
    # system, I'd use something more fancy.  But for this purpose this
    # is easy to write and easy to verify that it's correct.
    # we loop through all of the dates by day, and then in each day we
    # loop over the alive people and check their status and put
    # them in a bucket.
    # If we detect the end of a month, we write a summary out and
    # clear out the buckets and start counting again.

    # person-days we have someone in each bucket for each month
    alive_ct = {}

    # people who died in each bucket in each month
    dead_ct = {}

    # this keeps track of the last bucket each person
    # was in, so we know where to put them when they die
    last_key = {}

    use_people = set()
    # this does a check for people with a ceartain number of
    # doses, you probably don't need this, but I used it for
    # some of my exploration.
    if n_vax is not None:
        print(f'filtering for people with exactly {n_vax} doses')
        for p in list(all_people):
            if len(vax_dates[p]) == n_vax:
                add = True
                for i in range(n_vax):
                    (vax_date, vax_dose, vax_batch) = vax_dates[p][i]
                    if vax_dose != i + 1:
                        add = False
                        break
                if add:
                    use_people.add(p)
        print(f'{len(use_people)} remaining from {len(all_people)}')
    else:
        use_people = all_people.copy()

    # here are the dates we loop over, I started early when I knew no
    # one would die so that I could make sure I was counting right
    # I also stop 60 days after the last date in the records, that
    # ensures that I close out a month properly.  Lazy, I know, but it works.
    start_date = datetime.date(2020, 1, 1)
    end_date = max(all_dates) + datetime.timedelta(days=60)

    # we'll start counting at the begnning of the earliest month in the data
    start_date = start_date.replace(day=1)

    # keep track of what month we're in so that we know when they switch months
    last_date_key = f'{start_date.year:04d}-{start_date.month:02d}'

    print(f'processing date range {start_date} to {end_date}...')
    # loop over the each day
    for offset in range((end_date - start_date).days + 1):
        # get the date we're currently working in
        cur_date = start_date + datetime.timedelta(days=offset)
        date_key = f'{cur_date.year:04d}-{cur_date.month:02d}'

        # if the date key changes, then we know we started a new month so
        # let's print out the end of month statistics
        # update: this just prints a status message now, we store the
        # date key with the actual data beacuse I needed the aggregated
        # data for something else later
        if (date_key != last_date_key):
            print(f'at the end of {last_date_key}, {len(use_people)} still alive')
            last_date_key = date_key

        # loop over the current people who are alive
        for p in list(use_people):
            # if this person dies add them to the death_bucket and
            # remove them from death_dates so we never process them again
            if p in death_dates and death_dates[p] < cur_date:
                if p in last_key:
                    dead_ct[last_key[p]] += 1
                use_people.remove(p)
                continue

            dose = 0
            week = 0
            batch = 0
            age = vax_age[p]

            # an inefficient way to do this, but it's fine for now
            # we sort the vax dates in reverse, and find the
            # dose number that the person is on today
            # and then calculate the bin (right now week) for how
            # long they lived
            if p in vax_dates:
                for (vax_date, vax_dose, vax_batch) in reversed(vax_dates[p]):
                    if vax_date > cur_date:
                        continue
                    dose = vax_dose
                    week = (cur_date - vax_date).days // 7
                    batch = vax_batch
                    break

            key = (date_key, dose, batch, week, age)

            # create the buckets if they don't exist yet
            if key not in alive_ct:
                alive_ct[key] = 0

            if key not in dead_ct:
                dead_ct[key] = 0

            # add a person day to the current bucket
            alive_ct[key] += 1

            # track the last bucket this person was in
            last_key[p] = key

    return (alive_ct, dead_ct)

#######################################
#######################################
#######################################


def print_buckets(filename, alive, dead, header=None):
    with open(filename, 'w') as out_file:
        if header:
            for h in header:
                print(h, end='\t', file=out_file)
            print('alive\tdead', file=out_file)
        for key in sorted(alive):
            for e in key:
                print(e, end='\t', file=out_file)
            print(f'{alive[key]}\t{dead[key]}', file=out_file)


#######################################
#######################################
#######################################

def regroup_buckets(alive_ct, dead_ct, new_key):
    # this takes the raw counts from the weekly buckets and a
    # function that will return the new buckets and it
    # regroups the counts into new keys
    alive_group = {}
    dead_group = {}

    for key in sorted(alive_ct):
        group_key = new_key(key)
        if (group_key not in alive_group):
            alive_group[group_key] = 0
        if (group_key not in dead_group):
            dead_group[group_key] = 0

        alive_group[group_key] += alive_ct[key]
        dead_group[group_key] += dead_ct[key]

    return (alive_group, dead_group)

#######################################
#######################################
#######################################


def no_batch(key):
    # removes date and age to make dose/week histograms
    (date_key, dose, batch, week, age) = key
    return (date_key, dose, week, age)


def dose_week(key):
    # removes date and age to make dose/week histograms
    (date_key, dose, batch, week, age) = key
    return (dose, week)


def all_ages(key):
    # removes age to get total counts
    (date_key, dose, batch, week, age) = key
    return (date_key, dose, week)


def stratify(weeks, years):
    # groups bins by weeks and ages by years
    _weeks = weeks
    _years = years

    def age_stratify(key):
        (date_key, dose, batch, week, age) = key
        return (date_key, dose, _weeks * (week // _weeks), _years * (age // _years))
    return age_stratify


def group_steve(key):
    # a grouping steve wanted
    (date_key, dose, batch, week, age) = key
    bin = 0
    if week >= 4:
        bin = 1
    if week >= 12:
        bin = 2
    if week >= 24:
        bin = 3
    return (date_key, dose, bin)


def group_month(key):
    # turn weeks into months
    (date_key, dose, batch, week, age) = key
    month = week // 4
    if month > 6:
        month = 6
    return (date_key, dose, month)

#######################################
#######################################
#######################################


# what source file to read - it has to have the format
# we got from the NZ data
if len(sys.argv) > 1:
    fname = sys.argv[1]
else:
    exit(0)

# a way to change the output file names
if len(sys.argv) > 2:
    prefix = sys.argv[2]
else:
    prefix = "ts"  # default prefix (ts for time-series)

# optional for printing out people
# with exactly number of vaccines
if len(sys.argv) > 3:
    n_vax = int(sys.argv[3])
else:
    n_vax = None

# really optional, if we arg 3 above, we may also want
# to filter out people who've skipped a vax dose
if len(sys.argv) > 4:
    do_filter = sys.argv[4] == 'FILTER'
else:
    do_filter = False

print(fname, prefix, n_vax, do_filter)

# lazy caching to make re-runs quick
if len(prefix) > 0:
    cache_path = f'{prefix}.pickle'
    prefix = prefix + '_'

if not os.path.exists(cache_path):
    print('reading data file...')
    read_nov9_csv(fname)
    print(f'{len(all_people)} people')
    print(f'{len(vaxxed_people)} vaxxed people')
    print(f'{len(unvaxxed_people)} unvaxxed people')
    print(f'{sum(len(v) for v in vax_dates.values())} vax doses')
    print(f'{len(death_dates)} death records')

    if do_filter:
        # remove people who may have skipped a dose or
        # at least don't have all of their doses in this
        # set of records
        print(f'filtering...')
        for p in list(all_people):
            if p not in vax_dates:
                all_people.remove(p)
            else:
                for i in range(len(vax_dates[p])):
                    (vax_date, vax_dose, vax_batch) = vax_dates[p][i]
                    if vax_dose != i + 1:
                        all_people.remove(p)
                        break

    print(f'remaining {len(all_people)} people')

    print('processing buckets...')
    (alive_ct, dead_ct) = make_buckets(n_vax=n_vax)
    with open(cache_path, 'wb') as f:
        pickle.dump((alive_ct, dead_ct), f)
else:
    print('reading cached data...')
    with open(cache_path, 'rb') as f:
        (alive_ct, dead_ct) = pickle.load(f)

print(f'{len(alive_ct)} buckets')

print('writing all bucket combinations...')
print_buckets(prefix + 'month_dose_batch_week_age.txt', alive_ct, dead_ct, header=['month', 'dose', 'batch', 'week', 'age'])
print('done...')

print('grouping by batch...')
(alive, dead) = regroup_buckets(alive_ct, dead_ct, no_batch)
print(f'{len(alive)} buckets')
print_buckets(prefix + 'month_dose_week_age.txt', alive, dead, header=['month', 'dose', 'week', 'age'])
print('done...')


print('grouping by all ages...')
(alive, dead) = regroup_buckets(alive_ct, dead_ct, all_ages)
print(f'{len(alive)} buckets')
print_buckets(prefix + 'month_dose_week.txt', alive, dead, header=['month', 'dose', 'week'])
print('done...')

print('age stratifying...')
(alive, dead) = regroup_buckets(alive_ct, dead_ct, stratify(1, 10))
print(f'{len(alive)} buckets')
print_buckets(prefix + 'month_dose_week_decade.txt', alive, dead, header=['month', 'dose', 'week', 'decade'])
print('done...')
