#
# docker makefile
#
 
$(if $(DOCKER_REGISTRY),,$(error DOCKER_REGISTRY is undefined))

registry = $(DOCKER_REGISTRY)
base_version = $(shell repo-release seven-testnet)

image_tag = $(registry)/$(project)
image = $(image_tag):latest

ape_tool_dir = ape/project/plugins/ape-tool
ape_tool_wheel = ape_tool-$(version)-py2.py3-none-any.whl
ape_tool_deps = $(wildcard $(ape_tool_dir)/ape_tool/*.py)
seven_common_wheel = $(notdir $(wildcard dist/seven_common*.whl))

build_opts = \
 --build-arg BASE_IMAGE=$(registry)/seven-base:$(base_version) \
 --build-arg APE_VERSION=$(APE_VERSION) \
 --build-arg VERSION=$(version) \
 --build-arg APE_TOOL_WHEEL=$(ape_tool_wheel) \
 --build-arg SEVEN_COMMON_WHEEL=$(seven_common_wheel) \
 --tag $(image_tag) \
 --progress plain

docker_deps = $(wildcard docker/*) \
	      docker/VERSION \
	      docker/setmountperms \
	      docker/$(ape_tool_wheel) \
	      docker/harambe.tgz \
	      docker/$(seven_common_wheel)
	
cleanup_files := docker/.build docker/VERSION docker/setmountperms docker/ape_tool* docker/*.whl

ape_files := project/ape-config.yaml project/Makefile project/bin project/contracts project/scripts

docker/harambe.tgz: $(addprefix ape/,$(ape_files))
	tar zcfv $@ -C ape $(ape_files)

docker/VERSION: VERSION
	cp $< $@

docker/setmountperms: bin/setmountperms
	cp $< $@

### copy common wheel to docker directory
docker/$(seven_common_wheel): dist/$(seven_common_wheel)
	cp $< $@

### copy plugin wheel to docker directory
docker/$(ape_tool_wheel): $(ape_tool_dir)/dist/$(ape_tool_wheel)
	cp $< $@

### build image
build: depends docker/.build

docker/.build: $(docker_deps) 
	docker build $(build_opts) docker | tee build.log
	docker tag $(image) $(image_tag):$(version)
	touch $@

### rebuild image
rebuild: clean depends
	$(MAKE) build_opts="$(build_opts) --no-cache" build

### docker-clean
docker-clean:
	rm -rf $(cleanup_files)

### docker-sterile
docker-sterile: docker-clean


### build plugin for docker image
$(ape_tool_dir)/dist/$(ape_tool_wheel): $(ape_tool_deps)
	rm -f docker/ape_tool*.whl
	{ cd $(ape_tool_dir); make wheel; }

### push image to docker registry
push: build release
	docker push $(image_tag):$(version)
	docker push $(image)

### container bash shell
shell:
	@ape shell

### run server in detached container
start:
	@ape daemon

### run foreground server
run:
	@ape server

### tail server log
tail:
	@while true; do if [ -n "$$(ape ps)" ]; then ape tail; else echo -n .; sleep 3; fi; done

### run the ape console
console:
	@ape console

### stop running server container
stop: 
	@ape kill

### show running containers
ps:
	@watch -n 1 ape ps
