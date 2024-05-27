import pandas as pd
import numpy as np

import isodate

import ifcopenshell
import ifcopenshell.api
path = '/home/20f82c13-9880-5efc-a643-e85321dbd70c/simple_house/ifc/4d.ifc'
f = ifcopenshell.open(path)

csv_path = '/'.join(path.split('/')[:-2])+'/4D/project_scheduling.csv'
wbs = pd.read_csv(csv_path)

wbs.replace({np.nan: None}, inplace=True)

def create_task_and_time(task_name, parent_task, start_date, duration, task_predefined_type):
    task = ifcopenshell.api.run('sequence.add_task', f, parent_task=parent_task, name=task_name, predefined_type=task_predefined_type)
    task_time = ifcopenshell.api.run('sequence.add_task_time', f, task=task)
    ifcopenshell.api.run('sequence.edit_task_time', f, task_time=task_time, attributes={'ScheduleStart':start_date, 'ScheduleDuration':duration})
    return task

#can include lagtime too. check docs for more info

def create_task_sequence(task, predecessor_id, sequence_code):
    predecessor = [t for t in f.by_type('IfcTask') if t.Identification==predecessor_id][0] 
    if sequence_code:
        if sequence_code == 'FS':
            sequence='FINISH_START'
        elif sequence_code=='SS':
            sequence='START_START'
    else:
        sequence='FINISH_START'
    ifcopenshell.api.run('sequence.assign_sequence', f, relating_process=predecessor, related_process=task, sequence_type=sequence)
    

work_plan = ifcopenshell.api.run('sequence.add_work_plan', f, name='Construction Plan')
schedule = ifcopenshell.api.run('sequence.add_work_schedule', f, name='Construction Schedule', work_plan=work_plan, predefined_type='PLANNED')


calendar = ifcopenshell.api.run('sequence.add_work_calendar', f, name='Work Calendar')
work_time = ifcopenshell.api.run('sequence.add_work_time', f, work_calendar=calendar, time_type='WorkingTimes')
ifcopenshell.api.run('sequence.edit_work_time', f, work_time=work_time, attributes={'Name':'9-6','Start':'2024-01-01', 'Finish':'2024-12-31'})
work_pattern = ifcopenshell.api.run('sequence.assign_recurrence_pattern', f, parent=work_time, recurrence_type='WEEKLY')
ifcopenshell.api.run('sequence.edit_recurrence_pattern', f, recurrence_pattern=work_pattern, attributes={'WeekdayComponent':list(range(1,6))})
ifcopenshell.api.run('sequence.add_time_period', f, recurrence_pattern=work_pattern, start_time='09:00', end_time='13:00')
ifcopenshell.api.run('sequence.add_time_period', f, recurrence_pattern=work_pattern, start_time='14:00', end_time='18:00')

holiday_time = ifcopenshell.api.run('sequence.add_work_time', f, work_calendar=calendar, time_type='ExceptionTimes')
ifcopenshell.api.run('sequence.edit_work_time', f, work_time=holiday_time, attributes={'Name':'Holidays','Start':'2024-01-01', 'Finish':'2024-12-31'})
holiday_pattern = ifcopenshell.api.run('sequence.assign_recurrence_pattern', f, parent=holiday_time, recurrence_type='YEARLY_BY_DAY_OF_MONTH')
ifcopenshell.api.run('sequence.edit_recurrence_pattern', f, recurrence_pattern=holiday_pattern, attributes={'DayComponent':[1], 'MonthComponent':[1]})


task_predefined_type = 'CONSTRUCTION' #TO TAKE FROM WBS
task_identification = 'C' # USEFUL ONLY FOR THE PARENT TASK
construction = ifcopenshell.api.run('sequence.add_task', f, work_schedule=schedule, name='Construction', identification=task_identification, predefined_type=task_predefined_type) #TO IDENTIFY PARENT TASK IN WBS
ifcopenshell.api.run('control.assign_control', f, relating_control=calendar, related_object=construction) #check this IfcRelAssignsToControl

for i in range(wbs.shape[0]):
    task_name=wbs.iloc[i]['Task Name']
    if wbs.iloc[i]['Parent Task'] == 'Construction':
        parent_task=construction
    start_date=wbs.iloc[i]['Start Date']
    duration_period=wbs.iloc[i]['Duration']
    duration = isodate.parse_duration(duration_period)
    task_predefined_type = 'CONSTRUCTION' #TO TAKE FROM WBS
    task = create_task_and_time(task_name, parent_task, start_date, duration, task_predefined_type)
    predecessor_id=wbs.iloc[i]['Predecessor']
    sequence_code=wbs.iloc[i]['Sequence'] 
    if predecessor_id:
        create_task_sequence(task, predecessor_id, sequence_code)
    else:
        continue

ifcopenshell.api.run('sequence.cascade_schedule', f, task=construction)

#ifcopenshell.api.run('sequence.assign_process')
#ifcopenshell.api.run('sequence.assign_product')
#ifcopenshell.api.run('sequence.assign_sequence')
#ifcopenshell.api.run('sequence.cascade_schedule')

f.write(path)
