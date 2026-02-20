from Components.workloads.workload import AR1Workload, AR1StrictLocalGroupWorkload, AR1ScheduledGroupIncast

workload_configuration = {
    "random_workload" : AR1Workload,
    "local_group_workload": AR1StrictLocalGroupWorkload,
    "incast": AR1ScheduledGroupIncast
}