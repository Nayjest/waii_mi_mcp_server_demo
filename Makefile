
start:
	docker-compose up -d
rebuild:
	docker stop waii_mcp
	docker-compose up --build -d
restart:
	docker-compose restart
logs:
	docker logs -f waii_mcp
sh:
	docker exec -it waii_mcp bash