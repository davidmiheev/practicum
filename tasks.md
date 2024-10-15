## Task 1
В Практикуме 60% студентов изучают программирование, а 40% - аналитику. Среди студентов, изучающих программирование, 70% успешно прошли тестирование по SQL. 
Тогда как среди студентов, изучающих аналитику, 80% успешно прошли этот тест. 
Если случайно выбранный студент успешно сдал тест по SQL, какова вероятность, что он изучает аналитику?

### Solution 
Пусть $`A`$ - случайно выбранный студент изучает программирование, $`B`$ - случайно выбранный студент изучает аналитику и $`C`$ - случайно выбранный студент прошёл тестирование по SQL.
Из условия мы знаем, что $`P(A) = 0.6`$, $`P(B) = 0.4`$, $`P(C|A) = 0.7`$, $`P(C|B) = 0.8`$
Нам нужно найти $`P(B|C)`$
Используем формулу Байеса: 
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

user_id (PK) - идентификатор студента на платформе

first_name - имя студента

last_name - фамилия студента

user_email - почта, на которую студент зарегистрирован в платформе

**tasks**:

task_id (PK) - идентификатор задачи

task_name - название задачи

module_name - название модуля, в котором расположена задача

course_name - название курса, в котором расположена задача

**attempts**:

user_id (PK) - идентификатор студента на платформе

task_id (PK) - идентификатор задачи

attempt_number (PK) - номер попытки сдачи задания, попытки нумеруются с 1

attempt_status - статус проверки задания. Возможные статусы: 
success - успешная сдача задания
fail - код выдает неверный ответ на задачу
error - код не запустился при попытке сдать задачу

Напишите запросы на SQL, которые позволят закрыть следующие бизнес-потребности:
- Найти список отстающих студентов. Студент, считается отстающим, если он сделал уже 4 попытки решить какую-либо задачу, но всё ещё не решил её. 
С этими студентами должен будет связаться наставник и помочь им в решении сложной задачи.

- Найти топ 5% самых трудных и самых простых задач в каждом курсе. Список этих задач будет передан в команду авторов курсов на рефакторинг.

### Solution

Первый запрос:
```sql
select s.user_id as student
from students as s
left join attempts as a
on s.user_id = a.user_id
group by s.user_id, task_id
having max(attempt_number) > 4 or (not array_contains(array_agg(attempt_status), 'success') and max(attempt_number) = 4)
```

Второй запрос: 
```sql
with task_complexity as (
select task_id, avg(attempts_number) as complexity
from attemts as a
group by task_id
),
ranked_tasks as (
select
  course_name,
  task_id,
  ROW_NUMBER() OVER (PARTITION BY course_name ORDER BY complexity DESC) AS rank,
  COUNT(*) OVER (PARTITION BY course_name) AS total_count
FROM tasks as t
left join task_complexity as tc
on t.task_id = tc.task_id
)
select
    course_name,
    task_id
FROM 
  ranked_tasks
WHERE 
    rank <= total_count * 0.05
ORDER BY 
    course_name, rank;
```
