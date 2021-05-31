# https://www.gnu.org/software/make/manual/html_node/Special-Variables.html
# https://ftp.gnu.org/old-gnu/Manuals/make-3.80/html_node/make_17.html
PROJECT_MKFILE_PATH       := $(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST))
PROJECT_MKFILE_DIR        := $(shell cd $(shell dirname $(PROJECT_MKFILE_PATH)); pwd)

PROJECT_NAME              := graphql_dsl
PROJECT_ROOT              := $(PROJECT_MKFILE_DIR)

BUILD_DIR                 := $(PROJECT_ROOT)/build
DIST_DIR                  := $(PROJECT_ROOT)/dist
TEST_DIR                  := $(PROJECT_ROOT)/tests

CLI                       := graphql-dsl


typecheck:
	mypy --config-file setup.cfg --package $(PROJECT_NAME)


test:
	pytest -s  --cov=$(PROJECT_NAME) $(TEST_DIR)


publish: test clean | do-publish
	@echo "Done publishing."


do-publish:
	python $(PROJECT_ROOT)/setup.py sdist bdist_wheel
	twine upload $(DIST_DIR)/*


test-all: | test
	@echo "Done."


clean:
	rm -rf $(BUILD_DIR) $(DIST_DIR)
