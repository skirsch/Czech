rm(list = ls()); gc()
if(!require(pacman)) install.packages("pacman")
pacman::p_unlock() ## removes any locks from failed installs.

update.packages(ask = FALSE)

## if update.packages fails, try remove.packages() for offending package
pacman::p_load(magrittr, tidyverse, epiDisplay, 
               rio, visdat, dataMaid, skimr, tidyr, survminer,
               foreach, doParallel)

df <- rio::import("../data/CR_records.csv", 
                  na.strings = c("", "NA"), 
                  strings.as.factors = FALSE)

# Create unique ID
df$ID <- row.names(df)

names(df) <- c("gender", 
               "yr_birth", 
               "date_death",
               "date_dose_1",
               "batch_1",
               "batch_1_code", 
               "dose_1_name",
               "date_dose_2",
               "batch_2",
               "batch_2_code",
               "dose_2_name",
               "date_dose_3",
               "batch_3",
               "batch_3_code",
               "dose_3_name",
               "date_dose_4", 
               "batch_4",
               "batch_4_code", 
               "dose_4_name",
               "date_dose_5", 
               "batch_5",
               "batch_5_code", 
               "dose_5_name",
               "date_dose_6",
               "batch_6",
               "batch_6_code", 
               "dose_6_name",
               "date_dose_7", 
               "batch_7",
               "batch_7_code", 
               "dose_7_name", "ID")

#load("Czech.rdata")

# duplicates----
# stopifnot(df[duplicated(df),]  |> nrow() == 0)
## no duplicates.
## ranges-----
# df |> skimr::skim()
## look at ranges

## Missing values-----
# df |> vis_miss(sort_miss = TRUE) +
#  ggplot2::theme(plot.margin = unit(c(1,3,1,1), "cm"))
## Review dataset in detail
#dataMaid::makeDataReport(df, replace = TRUE)

## operate on first 10,000 records



df <- df[sample(1:nrow(df), 3000000), ]
#df |> skimr::skim()

start_date <- min(df$date_death, na.rm = TRUE)
start_date
end_date <- max(df$date_death, na.rm = TRUE)
end_date |> str()

df$date_dose_0 <- start_date

df |> head()
## change wide to long dataset----
dfl <- pivot_longer(df, 
                    cols = starts_with("date_dose_", 
                                       vars = NULL), 
                    values_to = "vax_date")

start_date <- min(df$date_death, na.rm = TRUE) |> as.POSIXct()
#start_date
end_date <- max(df$date_death, na.rm = TRUE)|> as.POSIXct()
#end_date |> str()


#dfl |> data.frame() |> head()
dfl$vax_dose <- substr(dfl$name, 11, 11) |> as.numeric()

rm(df); gc();

# Estimate maximum dose for each individual.
dose_max <- aggregate(vax_dose ~ ID, data = dfl[!is.na(dfl$vax_date),], 
                      FUN = max)

names(dose_max) <- c("ID", "max_dose")

dflm <- merge(dfl, dose_max, by = "ID", all.x = TRUE)

dflm |> head(300)

dflm <- dflm[order(dflm$ID, dflm$vax_dose ),]
#dflm |> head(100)
dflm$date_death <- as.POSIXct(dflm$date_death)
dflm$vax_date <- as.POSIXct(dflm$vax_date)
#dflm$date_death |> summary()

dflm$startDate <- ifelse(dflm$vax_dose == 0, start_date, 
                         dflm$vax_date) |> as.POSIXct()
dflm <- dflm[!is.na(dflm$startDate), ]
#dflm <- dflm[, -ncol(dflm)]
end_date <- end_date |> as.POSIXct()
#end_date |> str()


dflm$endDate <- NULL
# for (i in 1:(nrow(dflm)-1)){
#   if(dflm$vax_dose[i] < dflm$max_dose[i]) {
#     dflm$endDate[i] <-  dflm$vax_date[i+1]
#   } else if (!is.na(dflm$date_death[i])){
#     dflm$endDate[i] <- dflm$date_death[i]
#   } else {
#     dflm$endDate[i] <- end_date
#   }}

## Try parallelise----

# Set up parallel backend
numCores <- detectCores() - 2 # Number of cores to use
cl <- makeCluster(numCores)
registerDoParallel(cl)

# Parallelized loop
foreach(i = 1:(nrow(dflm)-1), .combine = "c") %dopar% {
  if(dflm$vax_dose[i] < dflm$max_dose[i]) {
    dflm$endDate[i] <-  dflm$vax_date[i+1]
  } else if (!is.na(dflm$date_death[i])){
    dflm$endDate[i] <- dflm$date_death[i]
  } else {
    dflm$endDate[i] <- end_date
  }
}

# Clean up parallel resources
stopCluster(cl)

## indicator variable
dflm$endDate <- as.Date(dflm$endDate |> as.POSIXct())
dflm$date_death <- as.Date(dflm$date_death |> as.POSIXct())

dflm$death <- ifelse(is.na(dflm$date_death), FALSE,
                     ifelse((dflm$max_dose == dflm$vax_dose), TRUE, FALSE))

dflm$death |> tab1()



###### get vax brand in parallel-----
numCores <- detectCores() - 2  # Use one less than the total number of cores
cl <- makeCluster(numCores)
registerDoParallel(cl)

dflm$vax_brand <- NA

dflm$vax_brand <- foreach(i = 1:nrow(dflm), .combine = c) %dopar% {
  if (dflm$vax_dose[i] == 0) {
    "None"
  } else {
    dflm[i, paste0("dose_", dflm$vax_dose[i], "_name")]
  }
}

# for (i in 1:nrow(dflm)){
#   if(dflm$vax_dose[i] == 0){
#     dflm$vax_brand[i] <-   "None"
#   } else {
#     dflm$vax_brand[i] <- dflm[i, paste0("dose_", dflm$vax_dose[i], "_name")]
#   }}

stopCluster(cl)


##############################################################

# dflm$vax_brand |> tab1(graph = FALSE)


## Assume all Czechs born in middle of year----
dflm$date_birth <- as.POSIXct(paste0(dflm$yr_birth, "-06-30"))


## Start age----
dflm$age_start <- difftime(dflm$startDate, dflm$date_birth, units = "days") |> 
  divide_by(365.25) |> as.numeric()


## End age----
dflm$age_end <- difftime(dflm$endDate, dflm$date_birth, units = "days") |> 
  divide_by(365.25)|> as.numeric()



#dflm[dflm$ID == 2506107,] |> head(200)


## simplify vax recording
dflm$vax <- ifelse(grepl("Comirnaty", dflm$vax_brand, ignore.case = TRUE), "Pfizer",
                   ifelse(grepl("Spikevax", dflm$vax_brand, ignore.case = TRUE),
                          "Moderna", 
                          ifelse(grepl("Janssen", dflm$vax_brand, ignore.case = TRUE),
                                 "Janssen", 
                                 ifelse(grepl("Nuvaxovid", dflm$vax_brand, ignore.case = TRUE),
                                        "Nuvaxovid", 
                                        ifelse(grepl("VAXZEVRIA", dflm$vax_brand, ignore.case = TRUE)|
                                                 grepl("Covishield", dflm$vax_brand, ignore.case = TRUE),
                                               "AZ",
                                               dflm$vax_brand)))))

dflm[dflm$vax_dose == 0, "vax"] <- "None"

dflm$vax <- dflm$vax |> as.factor() |> relevel(ref = "None")
dflm$vax |> tab1()
dev.off(); plot.new()

dflm <- dflm[!(dflm$vax == "Nuvaxovid"|
                 dflm$vax == "Sinopharm"| 
                 dflm$vax == "Sinovac"|
                 dflm$vax == "COVAXIN"|
                 dflm$vax == "Covovax"|
                 dflm$vax == "Sputnik V"), ]
dflm$vax <- dflm$vax |> droplevels()

dflm <- dflm[!(dflm$vax == "None" & dflm$vax_dose > 0), ]

dflm$vax |> tab1()

dflm |> head(100)

kmfit <- survfit(Surv(age_start, age_end, death) ~ vax,
                 data = dflm)
plot(kmfit, mark.time=FALSE, lty=1:5,
     xlab="Age at event", 
     ylab="Survival",
     main = "Left truncated survival analysis,
     1,000,000 randomly selected records,
     Age as time scale,
     Czech data",
     col = 1:5,
     lwd = 1.5,
     ylim = c(0, 1))
legend(0, .6, levels(dflm$vax), 
       lty = c(1:5), 
       col=1:5)



survminer::ggsurvplot(kmfit, data = dflm, 
                      risk.table = FALSE,
                      conf.int = TRUE,
                      conf.int.alpha = 0.1,
                      ylim = c(0,100),
                      cumevents = TRUE,
                      censor = FALSE,
                      #break.time.by = 5,
                      fontsize = 3, 
                      xlab = "Age at event", 
                      fun = "pct",
                      title = "")


## Select those with only Pfizer or only Moderna

dfS <- aggregate(vax ~ ID, data = dflm, 
                 FUN = paste)
dfS$vax |> str()
vax_order <- do.call(rbind, dfS$vax)
vax_order <- vax_order |> data.frame()
cols <- names(vax_order)
cols
x <- do.call(paste, c(vax_order[cols], sep="-"))
x |> head(1000)

dfS[995,]
dfS |> head()
dfS$vax <- do.call(rbind, dfS$vax)
dfS$vax |> head(100)
dfS$vax_history <- x
dfS$Pfizer_Moderna <- grepl("Pfizer", dfS$vax_history) & grepl("Moderna", dfS$vax_history)
dfS$Pfizer_Moderna |> tab1()
dfS$vax_history |> tab1(graph = FALSE)

# Pure dataset
dfP <- merge(dflm, dfS[, c("ID", "Pfizer_Moderna", "vax_history")], by = "ID", all.x = TRUE)
dfP <- dfP[dfP$Pfizer_Moderna == FALSE,]
dfP$vax_history |> tab1(graph = FALSE)
kmfit <- survfit(Surv(age_start, age_end, death) ~ vax,
                 data = dfP)
plot(kmfit, mark.time=FALSE, lty=1:5,
     xlab="Age at event", 
     ylab="Survival",
     main = "Left truncated survival analysis, 
     1,000,000 records, mixed cohort removed,
     Age as time scale,
     Czech data",
     col = 1:5,
     lwd = 1.5,
     ylim = c(0, 1))
legend(0, .6, levels(dflm$vax), 
       lty = c(1:5), 
       col=1:5)

## Pfizer & Moderna only----
dfPf <- dfP[dfP$vax_history == "None-Pfizer-Pfizer-Pfizer-Pfizer-Pfizer-Pfizer-Pfizer"|
             dfP$vax_history == "None-Pfizer-Pfizer-Pfizer-Pfizer-Pfizer-None-Pfizer"|
             dfP$vax_history == "None-Pfizer-Pfizer-Pfizer-Pfizer-None-Pfizer-Pfizer"|
             dfP$vax_history == "None-Pfizer-Pfizer-Pfizer-None-Pfizer-Pfizer-Pfizer"|
             dfP$vax_history == "None-Pfizer-Pfizer-None-Pfizer-Pfizer-None-Pfizer"|
             dfP$vax_history == "None-Pfizer-None-Pfizer-None-Pfizer-None-Pfizer"|
             dfP$vax_history == "None-None-None-None-None-None-None-None"|
              dfP$vax_history == "None-Moderna-Moderna-Moderna-Moderna-Moderna-Moderna-Moderna"|
              dfP$vax_history == "None-Moderna-Moderna-Moderna-Moderna-Moderna-None-Moderna"|
              dfP$vax_history == "None-Moderna-Moderna-Moderna-Moderna-None-Moderna-Moderna"|
              dfP$vax_history == "None-Moderna-Moderna-Moderna-None-Moderna-Moderna-Moderna"|
              dfP$vax_history == "None-Moderna-Moderna-None-Moderna-Moderna-None-Moderna"|
              dfP$vax_history == "None-Moderna-None-Moderna-None-Moderna-None-Moderna"|
              dfP$vax_history == "None-None-None-None-None-None-None-None",]

dfPf$vax_dose_brand <- paste0(dfPf$vax_dose, "_", dfPf$vax)

kmfit <- survfit(Surv(age_start, age_end, death) ~ vax_dose_brand,
                 data = dfPf)
dev.off(); plot.new()
plot(kmfit, mark.time=FALSE, lty=1:14, cex.main = 0.8,
     xlab="Age at death", 
     ylab="Survival",
     main = "Left-truncated survival analysis, 
     3M random records, Pfizer & Moderna by dose, mixed and other jabs excluded
     Age as time scale,
     Czech data",
     col = 1:14,
     lwd = 2,
     ylim = c(0, 1),
     xlim = c(0, 100))
legend(0, .8, levels(dfPf$vax_dose_brand |> factor()), 
       lty = c(1:14), cex = 0.8, lwd = 2,
       col=1:14)
survminer::ggsurvplot(kmfit, data = dfPf, 
                      #risk.table = TRUE,
                      conf.int = TRUE,
                      conf.int.alpha = 0.1,
                      ylim = c(20,100),
                      cumevents = TRUE,
                      censor = FALSE,
                      break.time.by = 10,
                      fontsize = 3, 
                      xlab = "Age at death", 
                      fun = "pct",
                      title = "Czech data (sampled to 1M);
                      Pfizer only cohort")

model <- coxph(Surv(age_start, age_end, death) ~ as.factor(vax_dose) + gender,
                 data = dfPf)
summary(model)


## Moderna only----
dfMo <- dfP[dfP$vax_history == "None-Moderna-Moderna-Moderna-Moderna-Moderna-Moderna-Moderna"|
              dfP$vax_history == "None-Moderna-Moderna-Moderna-Moderna-Moderna-None-Moderna"|
              dfP$vax_history == "None-Moderna-Moderna-Moderna-Moderna-None-Moderna-Moderna"|
              dfP$vax_history == "None-Moderna-Moderna-Moderna-None-Moderna-Moderna-Moderna"|
              dfP$vax_history == "None-Moderna-Moderna-None-Moderna-Moderna-None-Moderna"|
              dfP$vax_history == "None-Moderna-None-Moderna-None-Moderna-None-Moderna"|
              dfP$vax_history == "None-None-None-None-None-None-None-None",]

dfMo$vax_dose_f <- dfMo$vax_dose |> factor() 
kmfit <- survfit(Surv(age_start, age_end, death) ~ vax_dose_f,
                 data = dfMo)
plot(kmfit, mark.time=FALSE, lty=1:8,
     xlab="Age at event", 
     ylab="Survival",
     main = "Left truncated survival analysis, 
     1,000,000 records, mixed cohort removed,
     Age as time scale,
     Czech data",
     col = 1:8,
     lwd = 1:8,
     ylim = c(0, 1))
legend(0, .8, levels(dfMo$vax_dose_f), 
       lty = c(1:7), 
       col=1:7)

survminer::ggsurvplot(kmfit, data = dfMo, 
                      risk.table = TRUE,
                      conf.int = TRUE,
                      conf.int.alpha = 0.1,
                      ylim = c(60,100),
                      cumevents = TRUE,
                      censor = FALSE,
                      break.time.by = 10,
                      fontsize = 3, 
                      xlab = "Age at death", 
                      fun = "pct",
                      title = "Czech data (sampled to 1M);
                      Moderna only cohort")



## AZ only----
dfAZ <- dfP[dfP$vax_history == "None-AZ-AZ-AZ-AZ-AZ-AZ-AZ"|
              dfP$vax_history == "None-AZ-AZ-AZ-AZ-AZ-None-AZ"|
              dfP$vax_history == "None-AZ-AZ-AZ-AZ-None-AZ-AZ"|
              dfP$vax_history == "None-AZ-AZ-AZ-None-AZ-AZ-AZ"|
              dfP$vax_history == "None-AZ-AZ-None-AZ-AZ-None-AZ"|
              dfP$vax_history == "None-AZ-None-AZ-None-AZ-None-AZ"|
              dfP$vax_history == "None-None-None-None-None-None-None-None",]


dfAZ$vax_dose_f <- dfAZ$vax_dose |> factor() 
kmfit <- survfit(Surv(age_start, age_end, death) ~ vax_dose_f,
                 data = dfAZ)
plot(kmfit, mark.time=FALSE, lty=1:8,
     xlab="Age at event", 
     ylab="Survival",
     main = "Left truncated survival analysis, 
     1,000,000 records, mixed cohort removed,
     Age as time scale,
     Czech data",
     col = 1:8,
     lwd = 1:8,
     ylim = c(0, 1))
legend(0, .8, levels(dfAZ$vax_dose_f), 
       lty = c(1:5), 
       col=1:5)

survminer::ggsurvplot(kmfit, data = dfAZ, 
                      risk.table = TRUE,
                      conf.int = TRUE,
                      conf.int.alpha = 0.1,
                      ylim = c(0,100),
                      cumevents = TRUE,
                      censor = FALSE,
                      break.time.by = 10,
                      fontsize = 3, 
                      xlab = "Age at death", 
                      fun = "pct",
                      title = "Czech data (sampled to 1M);
                      AZ only cohort")



save(list = ls(), file = "Czech.rdata")
