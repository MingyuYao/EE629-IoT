FROM python:alpine3.7 
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt && \
	export FLASK_APP=flaskr && \
	export FLASK_ENV=development && \
	flask init-db
EXPOSE 5000
ENTRYPOINT [ "flask" ] 
CMD [ "run" ] 
