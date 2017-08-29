#!/usr/bin/env bats

@test "salt-call binary is in our \$PATH" {
  command -v salt-call
}

@test "salt-call version is 2016.11.7" {
  run salt-call --version
  echo "Salt version found is ${lines[0]}"
  [[ ${lines[0]} =~ "2016.11.7" ]]
}

@test "assert pillar renders" {
  run salt-call pillar.items > /dev/null
  [ ${status} = 0 ]
}

