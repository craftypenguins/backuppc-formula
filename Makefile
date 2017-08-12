SHELL=/bin/bash
FORMULA=backuppc
PILLAR=pillar.example
lxc_image_base=ubuntu:16.04
lxc_image_name=saltsolo
lxc_image_description="Salt Masterless Minion for Testing - based on $(lxc_image_base)"
test_container_name=saltsolo
LXC_IMAGE_INFO:=$(shell lxc image list | grep $(lxc_image_name))
ROOT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
INTEGRATION_TESTSUITE=default
#Used to generate newline in builtin error output
define n


endef


# Test for required programs to run this make
EXECUTABLES = jq lxc lxd
K := $(foreach exec,$(EXECUTABLES),\
	        $(if $(shell which $(exec)),some string,$(error "No $(exec) in PATH")))

.PHONY: all dist-clean clean clean-test image test-lxc-setup venv test
all: build test package

dist-clean:	clean
	@lxc image list $(lxc_image_name) | grep -q $(lxc_image_name) && lxc image delete $(lxc_image_name) || true
	@[ -d $(ROOT_DIR)/.virtualenv ] && rm -rf $(ROOT_DIR)/.virtualenv || true

clean:	clean-test

clean-test:
	@lxc list $(test_container_name) | grep -q $(test_container_name) && lxc delete -f $(test_container_name) || true
	@[ -f $(ROOT_DIR)/ssh_config ] && rm $(ROOT_DIR)/ssh_config || true

# Virtualenv Builder
venv: $(ROOT_DIR)/.virtualenv/bin/activate

$(ROOT_DIR)/.virtualenv/bin/activate:
	test -d .virtualenv || python3 -m venv .virtualenv
	.virtualenv/bin/pip install -U pip setuptools
	.virtualenv/bin/pip install -Ur test_requirements.txt
	touch .virtualenv/bin/activate

# LXC Image Builder
image: 
ifeq ($(shell lxc info preseed 1>/dev/null 2>&1 && echo exists), exists)
	$(error "A `preseed` container already exists$(n)Remove existing preseed container$(n)lxc delete preseed -f")
endif
ifeq ($(shell lxc image list | grep -q saltsolo && echo exists), exists)
	$(error "An image named saltsolo already exists$(n)Remove existing saltsolo image before building$(n)lxc image delete saltsolo")
endif
	@lxc launch $(lxc_image_base) preseed 
	@lxc exec preseed -- bash -c "while [ ! -d /root/.ssh ]; do sleep 1; done"  #Added this because there have been race issues where IP exists, but not /root/
	@echo "Setting up BATS PPA"
	@lxc exec preseed -- bash -c "add-apt-repository ppa:duggan/bats --yes"
	@echo "Setting up Salt Repository"
	@lxc exec preseed -- bash -c "wget -q -O - https://repo.saltstack.com/apt/ubuntu/16.04/amd64/latest/SALTSTACK-GPG-KEY.pub | apt-key add -"
	@lxc exec preseed -- bash -c "echo 'deb http://repo.saltstack.com/apt/ubuntu/16.04/amd64/latest xenial main' > /etc/apt/sources.list.d/saltstack.list"
	@echo "Updating System to latest and installing Salt Minion, BATS"
	@lxc exec preseed -- bash -c "apt-get -qq update && apt-get -qq -y dist-upgrade && apt-get -qq install -y salt-minion bats"
	@lxc exec preseed -- bash -c "mkdir -p /srv/saltstack/formulas"
	@lxc exec preseed -- bash -c "mkdir -p /srv/saltstack/pillar"
	@lxc exec preseed -- bash -c "mkdir -p /srv/saltstack/salt"
	@echo "Turning off systemd automatic apt-get update runs by schedule - causes race conditions on salt runs"
	@lxc exec preseed -- bash -c "systemctl disable apt-daily.service # disable run when system boot"
	@lxc exec preseed -- bash -c "systemctl disable apt-daily.timer   # disable timer run"

	@lxc stop preseed
	@echo "Publishing image $(lxc_image_name)"
	@lxc publish preseed --alias $(lxc_image_name) description=$(lxc_image_description)
	@echo "Cleaning up preseed image"
	@lxc delete preseed

ifeq (, $(LXC_IMAGE_INFO))
test-lxc-setup: image
endif
test-lxc-setup:
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
	-@lxc config device add $(test_container_name) minion disk source=$(ROOT_DIR)/test/minion path=/etc/salt
	-@lxc config device add $(test_container_name) salt disk source=$(ROOT_DIR)/test/salt path=/srv/saltstack/salt
	-@lxc config device add $(test_container_name) pillar disk source=$(ROOT_DIR)/test/pillar path=/srv/saltstack/pillar
	-@lxc config device add $(test_container_name) test disk source=$(ROOT_DIR)/test path=/test
	-@lxc config device add $(test_container_name) $(FORMULA) disk source=$(ROOT_DIR)/$(FORMULA) path=/srv/saltstack/formulas/$(FORMULA)
	@echo "Restarting container minion"
	@lxc exec $(test_container_name) -- service salt-minion restart

test-lxc-run: container_ip=$(shell lxc list $(test_container_name) --format json | jq -r '.[] .state.network.eth0.addresses[0].address')
test-lxc-run: $(ROOT_DIR)/ssh_config
test-lxc-run: test-lxc-run-testinfra
test-lxc-run: test-lxc-run-infrastructure
#test-lxc-run: test-lxc-run-salt
#test-lxc-run: test-lxc-run-ssh

test-lxc-run-testinfra: container_ip=$(shell lxc list $(test_container_name) --format json | jq -r '.[] .state.network.eth0.addresses[0].address')
test-lxc-run-testinfra: $(ROOT_DIR)/ssh_config
	@.virtualenv/bin/pytest -s -v --ssh-config=$(ROOT_DIR)/ssh_config --hosts=saltsolo $(ROOT_DIR)/test/pytest

test-lxc-run-salt:
	@ssh -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@$(container_ip) -C 'salt-call --local state.sls backuppc'

test-lxc-run-infrastructure:
	@echo "Running BATS $(INTEGRATION_TESTSUITE) tests"
	@ssh -q -F $(ROOT_DIR)/ssh_config root@$(container_ip) -C 'bats /test/integration/$(INTEGRATION_TESTSUITE)/bats'

$(ROOT_DIR)/ssh_config: container_ip=$(shell lxc list $(test_container_name) --format json | jq -r '.[] .state.network.eth0.addresses[0].address')
$(ROOT_DIR)/ssh_config: 
	@echo "Building SSH config file for tests"
	@echo "StrictHostKeyChecking no" > $(ROOT_DIR)/ssh_config
	@echo "Host saltsolo" >> $(ROOT_DIR)/ssh_config
	@echo "  hostname $(container_ip)" >> $(ROOT_DIR)/ssh_config
	@echo "  user root" >> $(ROOT_DIR)/ssh_config

#todo - Add a test-verbose so that the pytests have -vv
test: venv test-lxc-setup test-lxc-run $(ROOT_DIR)/ssh_config
	@echo "Tests done"

build:
	$(eval test_container_ip = $$(shell lxc list $(test_container_name) --format json | jq -r ".[] .state.network.eth0.addresses[0].address" ))
	@echo "Container up at IP $(test_container_ip)"

package:
	@echo "Packaging formula"
	
