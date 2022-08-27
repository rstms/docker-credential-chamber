#
# docker makefile
#
 
exec = chamber exec $(PROFILE) --

build_args := \
 BASE_IMAGE=$(registry)/seven-base:latest \
 VERSION=$(version)

image = $(registry)/$(repo)

build_arg_list = $(foreach arg,$(build_args),--build-arg $(arg) )

build_opts := $(build_arg_list) --tag $(image):$(version)

build_env:
	@echo "registry=$(registry)"
	@echo "base_version=$(version)"
	@echo "version=$(version)"
	@echo "build_args=$(build_args)"
	@echo "build_arg_list=$(build_arg_list)"
	@echo "build_opts=$(build_opts)"

env:
	@chamber env $(PROFILE)

## build docker image
build: release
	docker build $(build_opts) .
	docker tag $(image):$(version) $(image):latest

## rebuild docker image
rebuild:
	$(MAKE) build_opts="$(build_opts) --no-cache" build

## push image to repository
push: build
	docker push $(image):$(version)
	docker push $(image):latest

## run image
docker-run: 
	$(exec) docker run $(image)

