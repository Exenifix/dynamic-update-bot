#!/bin/bash
set -e

container_name=dynamic-update-bot

readarray -t critical_files < <(yq '.critical_files[]' .github/deploy/deploy-config.yaml)
changed_files=$(git diff --name-only HEAD~1 HEAD)
restart_required=false
container_active=false
if [ $( docker ps -a | grep $container_name | wc -l ) -gt 0 ] && [ docker inspect -f '{{.State.Running}}' $container_name ]; then
  container_active=true
fi

# if there's no container no need to check for files
if [ "$container_active" = true ]; then
  for file in "${critical_files[@]}"; do
    if [[ "$changed_files" =~ "$file" ]]; then
      restart_required=true
      break
    fi
  done
else
  restart_required=true
fi

if [ "$restart_required" = true ]; then
  if [ "$container_active" = true ]; then
    echo "Detected changes in critical files, performing complete restart."
  else
    echo "Container is not up, performing first run."
  fi
  docker compose up -d --build
  python3 -m exendlr bobux-prod "ready"
  docker image prune -f
else
  echo "No changes in critical files, applying update without restart."
  curl -X POST -H "Authorisation: $API_SECRET" http://localhost:3030/update
fi
