SHELL=/bin/bash
lxc_image_name = "ubuntu:16.04"
test_container_name = "saltsolo"

# Test for required programs to run this make
EXECUTABLES = jq lxc lxd
K := $(foreach exec,$(EXECUTABLES),\
	        $(if $(shell which $(exec)),some string,$(error "No $(exec) in PATH")))

# Check LXC/LXD prerequisites
check-lxc-prereq:
ifeq (, $(shell which lxd))
	$(error "No LXD in $(PATH), consider installing LXD/LXC packages")
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
	lxc delete $(test_container_name)

flarn:
	@echo Container exists ? $(test_container_exists)
	@echo "Test done"

test-lxc: test-lxc-announce check-lxc-prereq test-lxc-wait
test-lxc: test-lxc-wait

test-lxc-announce:
	@echo "================================"
	@echo "Setting up LXC test environment"

test-lxc-launch:
	@echo "Launching $(test_container_name) LXC test environment"
	@lxc launch $(lxc_image_name) $(test_container_name)

test-lxc-exists:
	$(eval test_container_exists := $(shell lxc info $(test_container_name) 1>/dev/null 2>&1; echo $$?))

#test-lxc-wait: test-lxc-exists
#ifeq (1, $(test_container_exists))
#test-lxc-wait: test-lxc-launch
#endif	
test-lxc-wait:
	@lxc info $(test_container_name) 1>/dev/null 2>&1 || \
		lxc launch $(lxc_image_name) $(test_container_name)
	@echo -n "Waiting for environment to have IP ."
	@while [[ ! "$$(lxc list $(test_container_name) --format json | jq -r '.[] .state.network.eth0.addresses[0].address' )" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$$ ]]; do echo -n "."; sleep 1; done
	@echo ""
	@sleep 3
	$(eval test_container_ip = $$(shell lxc list $(test_container_name) --format json | jq -r ".[] .state.network.eth0.addresses[0].address" ))
	@echo "Container up at IP $(test_container_ip)"

test: test-lxc
test: test_container_ip = $(shell lxc list $(test_container_name) --format json | jq -r ".[] .state.network.eth0.addresses[0].address" )
	@echo "Container up at IP $(test_container_ip)"
	@echo "Tests done"

build:
	$(eval test_container_ip = $$(shell lxc list $(test_container_name) --format json | jq -r ".[] .state.network.eth0.addresses[0].address" ))
	@echo "Container up at IP $(test_container_ip)"

	
