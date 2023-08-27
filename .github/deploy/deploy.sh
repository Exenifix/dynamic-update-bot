#!/bin/bash
set -e

container_name=dynamic-update-bot

docker_restart() {
  echo "Running docker compose..."
  docker compose up -d --build
  python3 -m exendlr $container_name "ready"
  docker image prune -f
  echo "Docker started"
}

update() {
  echo "Performing request to running bot..."
  curl -X POST -H "Authorisation: $API_SECRET" http://localhost:3030/update
  echo "Request done"
}

echo "Pulling from remote..."
prev_commit=$(git rev-parse HEAD)
git pull -fq
new_commit=$(git rev-parse HEAD)
echo "Successfully pulled, ${prev_commit:0:7}...${new_commit:0:7}"

echo "Checking container activity..."
container_active=false
if [ $( docker ps -a | grep $container_name | wc -l ) -gt 0 ] && [ docker inspect -f '{{.State.Running}}' $container_name ]; then
  container_active=true
fi
echo ((container_active="true" ? "Container active" : "Container inactive"))
if [ "$container_active" = false ]; then
  docker_restart
  exit 0
fi

if [ "$prev_commit" != "$new_commit" ]; then
  echo "Checking changed files..."
  changed_files=$(git diff --name-only $prev_commit HEAD)
  readarray -t critical_files < <(yq '.critical_files[]' .github/deploy/deploy-config.yaml)
  for file in "${critical_files[@]}"; do
    if [[ "$changed_files" =~ "$file" ]]; then
      echo "Found changes in critical files, performing complete restart..."
      docker_restart
      exit 0
    fi
  done
else
  echo "Pull did not update any files, ignoring update"
  exit 0
fi

echo "No changes in critical files, applying update without restart."
update
