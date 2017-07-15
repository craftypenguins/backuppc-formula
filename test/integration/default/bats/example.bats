#!/usr/bin/env bats

@test "salt-call binary is in our \$PATH" {
  command -v salt-call
}

@test "salt-call version is 2016.11.6" {
  run salt-call --version
  [[ ${lines[0]} =~ "2016.11.6" ]]
}

@test "assert pillar renders" {
  run salt-call pillar.items > /dev/null
  [ ${status} = 0 ]
}

