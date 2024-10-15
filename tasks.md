## Task 1
В Практикуме 60% студентов изучают программирование, а 40% - аналитику. Среди студентов, изучающих программирование, 70% успешно прошли тестирование по SQL. 
Тогда как среди студентов, изучающих аналитику, 80% успешно прошли этот тест. 
Если случайно выбранный студент успешно сдал тест по SQL, какова вероятность, что он изучает аналитику?

### Solution 
Пусть $`A`$ - случайно выбранный студент изучает программирование, $`B`$ - случайно выбранный студент изучает аналитику и $`C`$ - случайно выбранный студент прошёл тестирование по SQL.
Из условия мы знаем, что $`P(A) = 0.6`$, $`P(B) = 0.4`$, $`P(C|A) = 0.7`$, $`P(C|B) = 0.8`$

Нам нужно найти $`P(B|C)`$

Для этого воспользуемся формулой Байеса: 
```math
P(B|C) = \frac{P(C|B)\cdot P(B)}{P(C)}
```
Теперь распишем $`P(C)`$ по формуле полной вероятности: 
```math
P(C) = P(C|A)P(A) + P(C|B)P(B)
```
И подставим в формулу Байеса: 
```math
P(B|C) = \frac{P(C|B)\cdot P(B)}{P(C|A)P(A) + P(C|B)P(B)}
```
По этой вычисляем ответ 
```math
P(B|C) = \frac{0.8\cdot 0.4}{0.7\cdot 0.6 + 0.8\cdot 0.4} = \frac{32}{74} = \frac{16}{37}
```

Ответ: $`\frac{16}{37}`$



## Task 2
Вам пришла задача: проанализировать успеваемость студентов по результатам сдачи задач в нашем тренажере. В базе есть следующие таблицы:

**students**:

- user_id (PK) - идентификатор студента на платформе

- first_name - имя студента

- last_name - фамилия студента

- user_email - почта, на которую студент зарегистрирован в платформе

**tasks**:

- task_id (PK) - идентификатор задачи

- task_name - название задачи

- module_name - название модуля, в котором расположена задача

- course_name - название курса, в котором расположена задача

**attempts**:

- user_id (PK) - идентификатор студента на платформе

- task_id (PK) - идентификатор задачи

- attempt_number (PK) - номер попытки сдачи задания, попытки нумеруются с 1

- attempt_status - статус проверки задания. Возможные статусы: 
    - success - успешная сдача задания
    - fail - код выдает неверный ответ на задачу
    - error - код не запустился при попытке сдать задачу

Напишите запросы на SQL, которые позволят закрыть следующие бизнес-потребности:
1. Найти список отстающих студентов. Студент, считается отстающим, если он сделал уже 4 попытки решить какую-либо задачу, но всё ещё не решил её. 
С этими студентами должен будет связаться наставник и помочь им в решении сложной задачи.

2. Найти топ 5% самых трудных и самых простых задач в каждом курсе. Список этих задач будет передан в команду авторов курсов на рефакторинг.

### Solution

1. Аггрегируем статусы попыток для которых их номер не превосходит 4 в массив и смотрим на его элементы. Первый запрос:
```sql
with user_task_attempts as (
select s.user_id, task_id, array_agg(attempt_status) as attempt_statuses
from students as s
left join attempts as a
on s.user_id = a.user_id
where attempt_number < 5
group by s.user_id, task_id
having (not array_contains(array_agg(attempt_status), 'success') and length(array_agg(attempt_status)) > 3)
)

select user_id as student, array_agg(task_id) as hard_tasks_for_student, array_agg(attempt_statuses) as attempt_statuses_for_student_on_hard_task
from user_task_attempts
group by user_id
order by user_id
```

2. Определяем сложность как количество попыток до первого успеха по всем пользователям для этой задачи, если задача так и не была никем решена определяем сложность как 100. Дальше ранжируем по убыванию сложности группируя по названию модуля + название курса. Второй запрос: 
```sql
WITH task_complexity as (
SELECT
    task_id,
    min(if(attempt_status = 'success', attempt_number, 100)) as complexity
FROM attempts as a
GROUP BY task_id
),
ranked_tasks as (
SELECT
  module_name || '_' || course_name as course_uid,
  t.task_id,
  complexity,
  ROW_NUMBER() OVER (PARTITION BY module_name || '_' || course_name ORDER BY complexity DESC) AS rank,
  COUNT(*) OVER (PARTITION BY module_name || '_' || course_name) AS total_count
FROM tasks as t
LEFT JOIN task_complexity as tc
ON t.task_id = tc.task_id
)
SELECT
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
```
