
build:
	docker build --no-cache -t "ghcr.io/brain-bican/tdt-cloud" .

run:
	docker run -p 8484:8080 -v /Users/hk9/Downloads/tdt_cloud:/code/taxonomies --env-file .env --rm -it ghcr.io/brain-bican/tdt-cloud