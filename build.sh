docker rmi km-rest || true
docker build -t km-rest .
docker stop km-rest || true
docker rm km-rest || true
docker run --name km-rest -p 8100:8282 -d --restart always --network dockers_default -e MONGO=mongodb  km-rest

