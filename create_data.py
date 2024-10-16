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
    'task_id': [f'TK{str(i).zfill(3)}' for i in range(1, 151)],  # 150 tasks
    'task_name': [f'Task {i}' for i in range(1, 151)],
    'module_name': [f'Module {random.randint(1, 2)}' for _ in range(150)],
    'course_name': [f'Course {random.randint(1, 3)}' for _ in range(150)]
}

tasks = pd.DataFrame(tasks_data)

# Generate sample data for attempts
attempts_data = {
    'user_id': [random.choice(students['user_id']) for _ in range(1200)],
    'task_id': [random.choice(tasks['task_id']) for _ in range(1200)],
    'attempt_number': [random.choice([1] * 10 + [2] * 20 + [3] * 10 + [4, 5, 6, 7, 8, 9, 10]) for _ in range(1200)],
    'attempt_status': [random.choice(['success'] * 30 + ['fail', 'error']) for _ in range(1200)]
}

attempts = pd.DataFrame(attempts_data)

def adjust_attepmts():
    adjusted_attempts = pd.DataFrame()
    for _, row in attempts.iterrows():
        user, task, att_num, att_status = row['user_id'], row['task_id'], row['attempt_number'], row['attempt_status']
        for i in range(1, att_num):
            if att_status != 'success':
                new_row_df = pd.DataFrame([{'user_id': user, 'task_id': task, 'attempt_number': i, 'attempt_status': random.choice(['fail', 'error'])}])
            else:
                new_row_df = pd.DataFrame([{'user_id': user, 'task_id': task, 'attempt_number': i, 'attempt_status': random.choice(['success'] * 2 + ['fail', 'error'])}])
            adjusted_attempts = pd.concat([adjusted_attempts, new_row_df], ignore_index=True)

        new_row_df = pd.DataFrame([{'user_id': user, 'task_id': task, 'attempt_number': att_num, 'attempt_status': att_status}])
        adjusted_attempts = pd.concat([adjusted_attempts, new_row_df], ignore_index=True)

    print(len(adjusted_attempts)) # total number of attempts
    return adjusted_attempts

attempts = adjust_attepmts()

# Display the DataFrames
print("Students DataFrame:")
print(students)
students.to_csv('students.csv', columns={'user_id', 'first_name', 'last_name', 'user_email'}, index=False)
print("\nTasks DataFrame:")
print(tasks)
tasks.to_csv('tasks.csv', columns={'task_id', 'task_name', 'module_name', 'course_name'}, index=False)
print("\nAttempts DataFrame:")
print(attempts)
attempts.to_csv('attempts.csv', columns={'user_id', 'task_id', 'attempt_number', 'attempt_status'}, index=False)
# print("\nCheck Attempts DataFrame:")
# print(attempts[attempts['task_id'] == 'TK005'])
# print("\nCheck Students DataFrame:")
# print(attempts[attempts['user_id'] == 'ST003'])

query_1 =  '''
with user_task_attempts as (
select s.user_id as user_id, task_id, array_agg(attempt_status) as attempt_statuses
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
with task_complexity_per_user as (
select task_id, user_id, min(if(attempt_status = 'success', attempt_number, 10)) as complexity_for_user
from attempts as a
group by task_id, user_id
),
task_complexity as (
select task_id, avg(complexity_for_user) as complexity
from task_complexity_per_user
group by task_id
),
ranked_tasks as (
select
  module_name || '_' || course_name as course_uid,
  t.task_id,
  complexity,
  DENSE_RANK() OVER (PARTITION BY module_name || '_' || course_name ORDER BY complexity DESC) AS rank,
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

query_3 = '''
with task_complexity_per_user as (
select task_id, user_id, min(if(attempt_status = 'success', attempt_number, 10)) as complexity_for_user
from attempts as a
group by task_id, user_id
),
task_complexity as (
select task_id, avg(complexity_for_user) as complexity
from task_complexity_per_user
group by task_id
),
ranked_tasks as (
select
  module_name || '_' || course_name as course_uid,
  t.task_id,
  complexity,
  DENSE_RANK() OVER (PARTITION BY module_name || '_' || course_name ORDER BY complexity ASC) AS rank,
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

result = duckdb.query(query_3).to_df()
print(result)
result.to_csv('very_easy_tasks.csv', columns = {'course_uid', 'task', 'rank', 'complexity'}, index=False)

query_4 = '''
with a as (
select
    s.user_id as user_id,
    first_name,
    last_name,
    user_email,
    task_id,
    attempt_number,
    attempt_status
from students as s
left join attempts as a
on s.user_id = a.user_id
)
select
    user_id as user_id,
    first_name,
    last_name,
    user_email,
    t.task_id as task_id,
    task_name,
    module_name,
    course_name,
    attempt_number,
    attempt_status
from a
right join tasks as t
on a.task_id = t.task_id
'''
result = duckdb.query(query_4).to_df()
print(result)
result.to_csv('joined_data.csv', columns = {'user_id', 'first_name', 'last_name', 'user_email', 'task_id', 'task_name', 'module_name', 'course_name', 'attempt_number', 'attempt_status'}, index=False)


query_5 = '''
with task_complexity_per_user as (
select task_id, s.user_id as user_id, first_name || ' ' || last_name as user_name, min(if(attempt_status = 'success', attempt_number, 10)) as complexity_for_user
from attempts as a
right join students as s
on a.user_id = s.user_id
group by task_id, s.user_id, user_name
)
select user_name, module_name, course_name, task_name, complexity_for_user
from task_complexity_per_user as tc
right join tasks as t
on tc.task_id = t.task_id
'''

result = duckdb.query(query_5).to_df()
print(result)
result.to_csv('student_performance.csv', columns = {'user_name', 'module_name', 'course_name', 'task_name', 'complexity_for_user'}, index=False)
