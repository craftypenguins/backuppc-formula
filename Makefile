SHELL=/bin/bash
FORMULA=backuppc
PILLAR=pillar.example
lxc_image_base=ubuntu:16.04
lxc_image_name=saltsolo
lxc_image_description="Salt Masterless Minion for Testing - based on $(lxc_image_base)"
test_container_name=saltsolo
ROOT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

# Test for required programs to run this make
EXECUTABLES = jq lxc lxd
K := $(foreach exec,$(EXECUTABLES),\
	        $(if $(shell which $(exec)),some string,$(error "No $(exec) in PATH")))

# Check LXC/LXD prerequisites
check-lxc-prereq:
ifeq (, $(shell lxc image list | grep saltsolo))
	$(error "No saltsolo in LXC images, 'make image' to generate one")
endif


.PHONY: all
all: build

.PHONY: increment
increment:

#Clean all
clean:	clean-test

#Clean Test Environment
clean-test:
	lxc stop $(test_container_name)

image: 
ifeq ($(shell lxc info preseed 1>/dev/null 2>&1 && echo exists), exists)
	$(error "A failed preseed container already exists - clean up and try again")
endif
ifeq ($(shell lxc image list | grep -q saltsolo && echo exists), exists)
	$(error "An image named saltsolo already exists - Not building")
endif
	@lxc launch $(lxc_image_base) preseed 
	@lxc exec preseed -- bash -c "while [ ! -d /root/.ssh ]; do sleep 1; done"  #Added this because there have been race issues where IP exists, but not /root/
	@echo "Setting up Salt Repository"
	@lxc exec preseed -- bash -c "wget -q -O - https://repo.saltstack.com/apt/ubuntu/16.04/amd64/latest/SALTSTACK-GPG-KEY.pub | apt-key add -"
	@lxc exec preseed -- bash -c "echo 'deb http://repo.saltstack.com/apt/ubuntu/16.04/amd64/latest xenial main' > /etc/apt/sources.list.d/saltstack.list"
	@echo "Updating System to latest and installing Salt Minion"
	@lxc exec preseed -- bash -c "apt-get -qq update && apt-get -qq -y dist-upgrade && apt-get -qq install -y salt-minion"
	@lxc exec preseed -- bash -c "mkdir -p /srv/saltstack/formulas"
	@lxc exec preseed -- bash -c "mkdir -p /srv/saltstack/pillar"
	@lxc exec preseed -- bash -c "mkdir -p /srv/saltstack/salt"
	@lxc stop preseed
	@echo "Publishing image $(lxc_image_name)"
	@lxc publish preseed --alias $(lxc_image_name) description=$(lxc_image_description)
	@echo "Cleaning up preseed image"
	@lxc delete preseed

test-lxc-setup: check-lxc-prereq 
	@echo "================================"
	@echo "Setting up LXC test environment"
	@lxc info $(test_container_name) 1>/dev/null 2>&1 || \
		lxc launch $(lxc_image_name) $(test_container_name) --ephemeral
	@echo -n "Waiting for environment to have IP ."
	@while [[ ! "$$(lxc list $(test_container_name) --format json | jq -r '.[] .state.network.eth0.addresses[0].address' )" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$$ ]]; do echo -n "."; sleep 1; done
	@echo ""
	@echo "Container up at IP $$(lxc list $(test_container_name) --format json | jq -r '.[] .state.network.eth0.addresses[0].address')"
	@echo "Adding current user key to root for SSH"
	@lxc exec $(test_container_name) -- bash -c "while ! pidof sshd >/dev/null ; do sleep 1; done" #Test for SSH running in contianer
	@sleep 1
	@lxc file push ~/.ssh/id_rsa.pub $(test_container_name)/root/.ssh/authorized_keys --mode=0600 --uid=0
	@echo "Mounting test fixtures"
	@lxc config device add $(test_container_name) minion disk source=$(ROOT_DIR)/test/minion path=/etc/salt
	@lxc config device add $(test_container_name) salt disk source=$(ROOT_DIR)/test/salt path=/srv/saltstack/salt
	@lxc config device add $(test_container_name) pillar disk source=$(ROOT_DIR)/test/pillar path=/srv/saltstack/pillar
	@lxc config device add $(test_container_name) $(FORMULA) disk source=$(ROOT_DIR)/$(FORMULA) path=/srv/saltstack/formulas/$(FORMULA)
	@echo "Restarting container minion"
	@lxc exec $(test_container_name) -- service salt-minion restart

test-lxc-run: container_ip=$(shell lxc list $(test_container_name) --format json | jq -r '.[] .state.network.eth0.addresses[0].address')
test-lxc-run: test-lxc-run-salt
test-lxc-run: test-lxc-run-ssh

test-lxc-run-salt:
	@ssh -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@$(container_ip) -C 'salt-call --local state.sls backuppc'

test-lxc-run-ssh:
	@ssh -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@$(container_ip) -C 'uptime'

test: test-lxc-setup test-lxc-run
	@echo "Tests done"

build:
	$(eval test_container_ip = $$(shell lxc list $(test_container_name) --format json | jq -r ".[] .state.network.eth0.addresses[0].address" ))
	@echo "Container up at IP $(test_container_ip)"

	
