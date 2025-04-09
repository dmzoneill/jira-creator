# --- Variables ---
deb_package_name := $(shell cat control | grep Package | sed 's/Package: //')
rpm_package_name := $(shell cat jira-creator.spec | grep Name | cut -d: -f 2 | tr -d ' ')
package_version := $(shell cat control | grep Version | sed 's/Version: //')
DEB_FILENAME := $(deb_package_name)_$(package_version).deb
RPM_FILENAME := $(rpm_package_name)-$(package_version)

SUPER_LINTER_CONFIGS = \
  .eslintrc.json \
  .htmlhintrc \
  .jscpd.json \
  .ruby-lint.yml \
  .stylelintrc.json

PYTHON ?= python
PIPENV ?= PIPENV_VERBOSITY=-1 PYTHONPATH=.:jira_creator COVERAGE_PROCESS_START=.coveragerc pipenv
SCRIPT := rh-jira.py

# --- Helper Target for Printing Headers ---
.PHONY: print-header
print-header:
	@echo "===================================="
	@echo "  Running Target: $(MAKECMDGOALS)"
	@echo "===================================="

# --- Setup & Install ---
.PHONY: install-linters
install-linters: print-header
	- sudo dnf install -y yamllint hadolint shellcheck
	- sudo apt install -y yamllint hadolint shellcheck
	- npm install jscpd textlint markdownlint hadolint
	$(PIPENV) run pip install pylint flake8 pyflakes black

.PHONY: install
install: print-header install-linters
	$(PIPENV) install --dev

.PHONY: setup
setup: print-header install
	@echo "✅ Virtualenv and dependencies ready."

# --- Run Script ---
.PHONY: run
run: print-header
	$(PIPENV) run $(PYTHON) $(SCRIPT)

.PHONY: dry-run
dry-run: print-header
	$(PIPENV) run $(PYTHON) $(SCRIPT) bug "Dry run summary" --dry-run

# --- Tests ---
.PHONY: test-setup
test-setup: print-header
	$(eval ENV_VARS := \
		"JPAT=NOT_A_SECRET" \
		"AI_PROVIDER=openai" \
		"JIRA_URL=https://issues.redhat.com" \
		"PROJECT_KEY=AAP" \
		"AFFECTS_VERSION=aa-latest" \
		"COMPONENT_NAME=analytics-hcc-service" \
		"PRIORITY=Normal" \
		"AI_API_KEY=NOT_A_SECRET" \
		"JIRA_BOARD_ID=21125" \
	)
	@for var in $(ENV_VARS); do echo $$var >> $$GITHUB_ENV; done

.PHONY: test
test: print-header coverage
	@echo "Running coverage"

.PHONY: test-watch
test-watch: print-header
	$(PIPENV) run ptw --onfail "notify-send 'Tests failed!'"

# --- Linting ---
.PHONY: lint
lint: print-header
	$(PIPENV) run isort .
	@echo "\n========== isort Finished =========="
	$(PIPENV) run autopep8 . --recursive --in-place --aggressive --aggressive
	@echo "\n========== autopep8 Finished =========="
	#$(PIPENV) run pylint $$PWD
	@echo "\n========== pylint Finished =========="
	#$(PIPENV) run flake8 $$PWD
	@echo "\n========== flake8 Finished =========="
	#$(PIPENV) run pyflakes $$PWD
	@echo "\n========== pyflakes Finished =========="
	$(PIPENV) run black $$PWD
	@echo "\n========== black Finished =========="
	#$(PIPENV) run yamllint $$PWD
	@echo "\n========== yamllint Finished =========="
	$(PIPENV) run hadolint $$PWD/Dockerfile
	@echo "\n========== hadolint Finished =========="
	#$(PIPENV) run markdownlint $$PWD/README.md
	@echo "\n========== markdownlint Finished =========="
	#$(PIPENV) run shellcheck $$PWD/README.md
	@echo "\n========== shellcheck Finished =========="
	./node_modules/jscpd/bin/jscpd -p "**/*.py" $$PWD
	@echo "\n========== jscpd Finished =========="

# --- Coverage ---
.PHONY: coverage
coverage: print-header
	- @. ./.test_vars && echo "Environment loaded"
	$(PIPENV) run coverage erase
	$(PIPENV) run coverage run -m pytest --durations=10 jira_creator/tests
	- $(PIPENV) run coverage combine
	$(PIPENV) run coverage report -m --fail-under=99
	$(PIPENV) run coverage html
	@echo "📂 Coverage report: open htmlcov/index.html"
	- @. ~/.bashrc.d/jpat.sh && echo "Environment restored"

# --- Coverage ---
.PHONY: coverage-docker
coverage-docker: print-header
	docker build -t jira_creator_unit -f Dockerfile.unittest .  # Build the Docker image
	docker run --rm -v $(PWD):/app -w /app --name coverage-container jira_creator_unit bash -c "\
		pipenv run coverage erase && \
		pipenv run coverage run -m pytest --durations=10 jira_creator/tests && \
		pipenv run coverage combine && \
		pipenv run coverage report -m --fail-under=99 && \
		pipenv run coverage html"  # Run all steps inside the container
	@echo "📂 Coverage report: open htmlcov/index.html"


# Clean up coverage artifacts
.PHONY: clean-coverage
clean-coverage: print-header
	rm -rf .coverage htmlcov

# --- Clean ---
.PHONY: clean
clean: print-header
	- find . -type d -name "jira_creator.egg-info" -exec rm -rf {} +
	- find . -type d -name "__pycache__" -exec rm -r {} +
	- find . -type f -name "*.pyc" -delete
	- find . -type f -name ".coverage*" -delete
	- find . -type f -name "coverage.xml" -delete
	- find . -type d -name ".pytest_cache" -exec rm -rf {} +
	- rm -rvf htmlcov
	- rm -rvf log.log
	- rm -rvf d_fake_seeder/log.log
	- rm -rvf .pytest_cache
	- rm -rvf debbuild
	- rm -rvf rpmbuild
	- rm -rvf *.deb
	- rm -rvf *.rpm
	- sudo rm -rvf .mypy_cache

# --- RPM / DEB Packaging ---
.PHONY: rpm
rpm: print-header clean
	- sudo dnf install -y rpm-build rpmlint python3-setuptools python3-setuptools
	rm -rvf ./rpmbuild
	mkdir -p ./rpmbuild/BUILD ./rpmbuild/BUILDROOT ./rpmbuild/RPMS ./rpmbuild/SOURCES ./rpmbuild/SPECS ./rpmbuild/SRPMS ./rpmbuild/SOURCE
	cp -r jira-creator.spec ./rpmbuild/SPECS/
	cp -r jira_creator/rh_jira.py ./rpmbuild/SOURCE/
	tar -czvf rpmbuild/SOURCES/$(RPM_FILENAME).tar.gz jira_creator/ 
	rpmbuild --define "_topdir `pwd`/rpmbuild" -v -ba ./rpmbuild/SPECS/jira-creator.spec

.PHONY: rpm-install
rpm-install: print-header rpm
	sudo dnf install rpmbuild/RPMS/<architecture>/python-example-1.0-1.<architecture>.rpm
	rpmlint

.PHONY: deb
deb: print-header clean
	sudo apt-get install dpkg dpkg-dev fakeroot
	sudo rm -rvf ./debbuild
	mkdir -vp ./debbuild/DEBIAN
	cp control ./debbuild/DEBIAN
	mkdir -vp ./debbuild/opt/jira-creator
	cp -r jira_creator/rh_jira.py ./debbuild/opt/
	touch ./debbuild/DEBIAN/postinst
	chmod 755 ./debbuild/DEBIAN/postinst

	sudo chown -R root:root debbuild
	fakeroot dpkg-deb --build debbuild $(DEB_FILENAME)

	dpkg -c $(DEB_FILENAME)
	dpkg -I $(DEB_FILENAME)

.PHONY: deb-install
deb-install: print-header deb	
	sudo dpkg -i $(DEB_FILENAME)

# --- Super Linter ---
.PHONY: super-lint
super-lint: print-header $(SUPER_LINTER_CONFIGS)
	docker run --rm \
	-e SUPER_LINTER_LINTER=error \
	-e LINTER_OUTPUT=error \
	-e LOG_LEVEL=ERROR \
	-e RUN_LOCAL=true \
	-e FILTER_REGEX_EXCLUDE="(^|/)\.git(/|$)" \
	-e GIT_IGNORE=true \
	-v $$(pwd):/tmp/lint \
	github/super-linter:latest --quiet

# --- External Linter Configs ---
.eslintrc.json:
	curl -sSL -o $@ https://raw.githubusercontent.com/dmzoneill/dmzoneill/main/.github/linters/.eslintrc.json

.htmlhintrc:
	curl -sSL -o $@ https://raw.githubusercontent.com/dmzoneill/dmzoneill/main/.github/linters/.htmlhintrc

.jscpd.json:
	curl -sSL -o $@ https://raw.githubusercontent.com/dmzoneill/dmzoneill/main/.github/linters/.jscpd.json

.ruby-lint.yml:
	curl -sSL -o $@ https://raw.githubusercontent.com/dmzoneill/dmzoneill/main/.github/linters/.ruby-lint.yml

.stylelintrc.json:
	curl -sSL -o $@ https://raw.githubusercontent.com/dmzoneill/dmzoneill/main/.github/linters/.stylelintrc.json

# --- Weaviate Setup ---
.PHONY: weaviate-setup
weaviate-setup: print-header
	docker run -d -p 8080:8080 semitechnologies/weaviate

# --- Help ---
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make install     - Install dependencies"
	@echo "  make setup       - Setup the environment"
	@echo "  make run         - Run the script"
	@echo "  make dry-run     - Run script in dry-run mode"
	@echo "  make test        - Run all unit tests"
	@echo "  make coverage    - Run coverage"
	@echo "  make lint        - Run format checks"
	@echo "  make super-lint  - Run super linter for more extensive lint"
	@echo "  make clean       - Remove __pycache__ and *.pyc files"
