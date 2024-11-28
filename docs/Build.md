# Docker Build & Run

```
docker build --no-cache -t "ghcr.io/brain-bican/tdt-cloud" .
```

```
docker run -p 8484:8080 -v /Users/hk9/Downloads/tdt_cloud:/code/taxonomies -it ghcr.io/brain-bican/tdt-cloud 
```

http://localhost:8484/api/init_taxonomy/human-neocortex-non-neuronal-cells
http://localhost:8484/api/browser/human-neocortex-non-neuronal-cells/table