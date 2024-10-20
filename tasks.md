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
По этой формуле вычисляем ответ:
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
WITH user_task_attempts as (
SELECT
    s.user_id,
    task_id,
    array_agg(attempt_status) as attempt_statuses
FROM students as s
LEFT JOIN attempts as a
ON s.user_id = a.user_id
WHERE attempt_number < 5
GROUP BY s.user_id, task_id
HAVING (not array_contains(array_agg(attempt_status), 'success') and length(array_agg(attempt_status)) > 3)
)

SELECT
    user_id as student,
    array_agg(task_id) as hard_tasks_for_student
FROM user_task_attempts
GROUP BY user_id
ORDER BY user_id
```

2. Определяем сложность как среднее количество попыток до первого успеха по всем пользователям для этой задачи, если задача так и не была никем решена определяем сложность как 10 (считаем что максимальное количество попыток по задаче 10). Дальше ранжируем по убыванию сложности группируя по названию модуля + название курса.
Запрос для вывода наиболее сложных задач:
```sql
WITH task_complexity_per_user as (
SELECT task_id, user_id, min(if(attempt_status = 'success', attempt_number, 10)) as complexity_for_user
FROM attempts as a
GROUP BY task_id, user_id
),
task_complexity as (
SELECT task_id, avg(complexity_for_user) as complexity
FROM task_complexity_per_user
GROUP BY task_id
),
ranked_tasks as (
SELECT
  module_name || '_' || course_name as course_uid,
  t.task_id,
  complexity,
  DENSE_RANK() OVER (PARTITION BY module_name || '_' || course_name ORDER BY complexity DESC) AS rank,
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
Запрос для вывода наиболее простых задач:
```sql
WITH task_complexity_per_user as (
SELECT task_id, user_id, min(if(attempt_status = 'success', attempt_number, 10)) as complexity_for_user
FROM attempts as a
GROUP BY task_id, user_id
),
task_complexity as (
SELECT task_id, avg(complexity_for_user) as complexity
FROM task_complexity_per_user
GROUP BY task_id
),
ranked_tasks as (
SELECT
  module_name || '_' || course_name as course_uid,
  t.task_id,
  complexity,
  DENSE_RANK() OVER (PARTITION BY module_name || '_' || course_name ORDER BY complexity ASC) AS rank,
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


## Task 3

Наши студенты учатся когортами - небольшими группами. В процессе они общаются друг с другом и с нашими сотрудниками: кураторами, наставниками и ревьюерами.

Куратор делает всё, чтобы каждый поступивший к нам студент смог добраться до конца обучения. Его работа начинается с момента оплаты обучения человеком и до получения диплома. То есть сначала он формирует список людей на зачисление и убеждается, что все смогли начать обучение. В процессе следит за отстающими и отрабатывает проблемы студентов. А заканчивает работать с когортой только после того, как все дошедшие до конца получили дипломы.

Разработайте дашборд для куратора, который он мог бы на ежедневной основе использовать для организации своей работы.

Дашборд можно сделать в Excel, GoogleSheets, DataLens или Tableau. Не забудьте выдать доступ по ссылке к получившемуся дашборду

### Solution

О дашборде:
- Язык дашборда: английский, считаем что наша платформа международная
- На дашборде есть 2 таба: Users (основная; эта вкладка про функциональность платформы, соответсвующей онлайн-школе) and Tasks (посвящён количеству и качеству заданий, размещённых на платформе)
- Более важные данные расположены выше, например контакты студентов или ключевые персональные метрики студентов по курсу
- Выделил ключевые персональные метрики: прогресс студента (пропорционален фидбэку от менторов и ревьюеров и числу решённых заданий) и частота встреч с менторами по курсу; можно смотреть изменение этих метрик с течением времени
- На вкладке Users есть раздел со списками студентов, которым возможно требуется уделить внимание (например, по причине замедленного прогресса по курсу или проблем с задачами)
- На вкладке Users можно найти раздел с запросами к куратору от студентов по курсу
- Также выделил метрики с помощью которых мы сравниваем насколько курс оказался качественным для разных студентов в когорте, а именно вовлечённость (involvement) и удовлетворённость (satisfaction)
- Все данные на дашборде будут обновляться в соответсвие с выбранным модулем и курсом.
Если вы выбираете несколько курсов, целый модуль или несколько модулей метрики будут усредняться или суммироваться (например, в случае с метрикой общего количества задач/попыток решить задачу). Также часть дашборда будет обновляться при выборе имени студента
- **Ссылка на сам дэшборд: https://datalens.yandex.cloud/0a76ph9e75een**
