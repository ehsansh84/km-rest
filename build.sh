#git pull
docker rmi km-rest 
docker build -t km-rest .
docker stop km-rest
docker rm km-rest
docker run --name km-rest -p 8100:8282 -d --restart always --network dockers_default -e MONGO=mongodb  km-rest

