SHELL=/bin/bash
lxc_image_name = "ubuntu:16.04"
test_container_name = "saltsolo"

.PHONY: all
all: build

.PHONY: increment
increment:
	echo $$(( $(buildversion) + 1 )) > version

#Check LXC/LXD prerequisites
check-lxc-prereq:
ifeq (, $(shell which lxd))
	$(error "No LXD in $(PATH), consider installing LXD/LXC packages")
endif

#Clean all
clean:	clean-test

#Clean Test Environment
clean-test:
		lxc stop saltsolo
		lxc delete saltsolo

test-lxc:	check-lxc-prereq test-lxc-launch test-lxc-wait

test-lxc-launch:
	@echo "Starting LXC test environment"
	@lxc launch $(lxc_image_name) $(test_container_name)

test-lxc-wait:
	@echo "Waiting for environment to have IP"
	@while [[ ! "$$(lxc list saltsolo --format json | jq '.[] .state.network.eth0.addresses[0].address' -r)" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$$ ]]; do echo -n "."; sleep 2; done
	$(eval test_container_ip = $$(shell lxc list saltsolo --format json | jq ".[] .state.network.eth0.addresses[0].address" -r))
	@echo "Container up at IP $(test_container_ip)"

test: test-lxc
	@echo "Container up at IP $(test_container_ip)"
	@echo "Test done"

build:
	$(eval test_container_ip = $$(shell lxc list saltsolo --format json | jq ".[] .state.network.eth0.addresses[0].address" -r))
	@echo "Container up at IP $(test_container_ip)"

	
