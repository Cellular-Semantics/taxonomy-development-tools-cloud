# Docker Build & Run

## Build

Run the following command to build the Docker image:

```
docker build --no-cache -t "ghcr.io/brain-bican/tdt-cloud" .
```

## Run

create an `.env` file with the following content:

```
GITHUB_TOKEN=your_github_token
ADMIN_SECRET=your_admin_secret
NEXTAUTH_SECRET=frontend auth secret
```

You can use [https://generate-secret.vercel.app/32](https://generate-secret.vercel.app/32) to generate a random secret. Note it privately as it is used to access the admin APIs.

Run the following command to run the Docker image:

```
docker run -p 8484:8080 -v /Users/hk9/Downloads/tdt_cloud:/code/taxonomies --env-file .env --rm -it ghcr.io/brain-bican/tdt-cloud 
```

See [API Documentation](Api.md) for more details on how to use the TDT Cloud endpoints.