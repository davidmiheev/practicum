import duckdb
import pandas as pd
import random

# Set a random seed for reproducibility
random.seed(42)

# Generate sample data for students
students_data = {
    'user_id': [f'ST{str(i).zfill(3)}' for i in range(1, 15)],  # 14 students
    'first_name': ['Alice', 'Bob', 'Charlie', 'David', 'Eva',
                   'Frank', 'Grace', 'Hannah', 'Ian', 'Jack', 'Alexey', 'Anna', 'Max', 'Eugene'],
    'last_name': ['Smith', 'Johnson', 'Williams', 'Jones', 'Brown',
                  'Davis', 'Miller', 'Wilson', 'Moore', 'Taylor', 'Ivanov', 'Grace', 'Ford', 'Red'],
    'user_email': [f'user{i}@example.com' for i in range(1, 15)]
}

students = pd.DataFrame(students_data)

# Generate sample data for tasks
tasks_data = {
    'task_id': [f'TK{str(i).zfill(3)}' for i in range(1, 111)],  # 110 tasks
    'task_name': [f'Task {i}' for i in range(1, 111)],
    'module_name': [f'Module {random.randint(1, 2)}' for _ in range(110)],
    'course_name': [f'Course {random.randint(1, 3)}' for _ in range(110)]
}

tasks = pd.DataFrame(tasks_data)

# Generate sample data for attempts
attempts_data = {
    'user_id': [random.choice(students['user_id']) for _ in range(80)],
    'task_id': [random.choice(tasks['task_id']) for _ in range(80)],
    'attempt_number': [random.randint(1, 5) for _ in range(80)],
    'attempt_status': [random.choice(['success', 'fail', 'error']) for _ in range(80)]
}

attempts = pd.DataFrame(attempts_data)

def adjust_attepmts():
    adjusted_attempts = pd.DataFrame()
    for _, row in attempts.iterrows():
        user, task, att_num, att_status = row['user_id'], row['task_id'], row['attempt_number'], row['attempt_status']
        for i in range(1, att_num):
            new_row_df = pd.DataFrame([{'user_id': user, 'task_id': task, 'attempt_number': i, 'attempt_status': random.choice(['success', 'fail', 'error'])}])
            adjusted_attempts = pd.concat([adjusted_attempts, new_row_df], ignore_index=True)

        new_row_df = pd.DataFrame([{'user_id': user, 'task_id': task, 'attempt_number': att_num, 'attempt_status': att_status}])
        adjusted_attempts = pd.concat([adjusted_attempts, new_row_df], ignore_index=True)

    print(len(adjusted_attempts))
    return adjusted_attempts

attempts = adjust_attepmts()

# Display the DataFrames
print("Students DataFrame:")
print(students)
students.to_csv('students.csv', columns={'user_id', 'first_name', 'last_name', 'user_email'}, index=False)
print("\nTasks DataFrame:")
print(tasks)
tasks.to_csv('tasks.csv',  columns={'task_id', 'task_name', 'module_name', 'course_name'}, index=False)
print("\nAttempts DataFrame:")
print(attempts)
attempts.to_csv('attempts.csv', columns={'user_id', 'task_id', 'attempt_number', 'attempt_status'}, index=False)
# print("\nCheck Attempts DataFrame:")
# print(attempts[attempts['task_id'] == 'TK005'])
# print("\nCheck Students DataFrame:")
# print(attempts[attempts['user_id'] == 'ST003'])

query_1 =  '''
with user_task_attempts as (
select s.user_id, task_id, array_agg(attempt_status) as attempt_statuses
from students as s
left join attempts as a
on s.user_id = a.user_id
where attempt_number < 5
group by s.user_id, task_id
having (not array_contains(array_agg(attempt_status), 'success') and length(array_agg(attempt_status)) > 3)
)

select user_id as student, array_agg(task_id) as hard_tasks_for_student
from user_task_attempts
group by user_id
order by user_id
'''
result = duckdb.query(query_1).to_df()
print(result)
result.to_csv('attention_to_this_students.csv', columns = {'student', 'hard_tasks_for_student'}, index=False)

query_2 = '''
with task_complexity as (
select task_id, min(if(attempt_status = 'success', attempt_number, 100)) as complexity
from attempts as a
group by task_id
),
ranked_tasks as (
select
  module_name || '_' || course_name as course_uid,
  t.task_id,
  complexity,
  ROW_NUMBER() OVER (PARTITION BY module_name || '_' || course_name ORDER BY complexity DESC) AS rank,
  COUNT(*) OVER (PARTITION BY module_name || '_' || course_name) AS total_count
FROM tasks as t
left join task_complexity as tc
on t.task_id = tc.task_id
)
select
    course_uid,
    task_id as task,
    rank,
    complexity
FROM
  ranked_tasks
WHERE
    rank <= total_count * 0.05
ORDER BY
    course_uid, rank;
'''

result = duckdb.query(query_2).to_df()
print(result)
result.to_csv('very_complex_tasks.csv', columns = {'course_uid', 'task', 'rank', 'complexity'}, index=False)
