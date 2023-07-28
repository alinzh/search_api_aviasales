#Указываем операц. систему
FROM ubuntu

#Устанавливаем Python и pipenv
RUN apt-get update
RUN apt-get install -y python3-setuptools python3-pip
#RUN apt-get install python3-pip
RUN pip install pipenv

# Задаем рабочую директорию
WORKDIR ./src
# Копируем содержимое данной папки в рабочую директорию
COPY . /src
# Устанавливаем зависимости
RUN pipenv install -r requirements.txt

# Устанавливаем tmux
RUN apt-get install -y tmux
RUN tmux attach
#CMD ["pipenv", "run", "python3", "bot.py"]
CMD ["tmux", "new-session", "-d", "pipenv", "run", "python3", "/src/bot.py"]



