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

# --- Setup & Install ---
.PHONY: install
install:
	npm install jscpd
	$(PIPENV) install --dev

.PHONY: setup
setup: install
	@echo "✅ Virtualenv and dependencies ready."

# --- Run Script ---
.PHONY: run
run:
	$(PIPENV) run $(PYTHON) $(SCRIPT)

# --- Create new readme ---
.PHONY: readme
readme:
	python3 create_readme.py

.PHONY: dry-run
dry-run:
	$(PIPENV) run $(PYTHON) $(SCRIPT) bug "Dry run summary" --dry-run

# --- Tests ---

.PHONY: test-setup
test-setup:
	echo "JPAT=NOT_A_SECRET" >> $$GITHUB_ENV
	echo "AI_PROVIDER=openai" >> $$GITHUB_ENV
	echo "JIRA_URL=https://issues.redhat.com" >> $$GITHUB_ENV
	echo "PROJECT_KEY=AAP" >> $$GITHUB_ENV
	echo "AFFECTS_VERSION=aa-latest" >> $$GITHUB_ENV
	echo "COMPONENT_NAME=analytics-hcc-service" >> $$GITHUB_ENV
	echo "PRIORITY=Normal" >> $$GITHUB_ENV
	echo "AI_API_KEY=NOT_A_SECRET" >> $$GITHUB_ENV
	echo "JIRA_BOARD_ID=21125" >> $$GITHUB_ENV

.PHONY: test
test: coverage
	echo Running coverage

.PHONY: test-watch
test-watch:
	$(PIPENV) run ptw --onfail "notify-send 'Tests failed!'"

# --- Lint ---
.PHONY: lint
lint:
	$(PIPENV) run black . --check
	$(PIPENV) run flake8 . --ignore=E501,F401,W503


.PHONY: format
format:
	node_modules/jscpd/bin/jscpd -p "**/*.py" $$PWD
	isort .
	$(PIPENV) run autopep8 . --recursive --in-place --aggressive --aggressive
	$(PIPENV) run black .

# Run tests with coverage, including subprocess tracking
.PHONY: coverage
coverage:
	$(PIPENV) run coverage erase
	$(PIPENV) run coverage run -m pytest --durations=10 jira_creator/tests
	- $(PIPENV) run coverage combine
	$(PIPENV) run coverage report -m --fail-under=99
	$(PIPENV) run coverage html
	@echo "📂 Coverage report: open htmlcov/index.html"


# Clean up coverage artifacts
clean-coverage:
	rm -rf .coverage htmlcov

# --- Clean ---
.PHONY: clean
clean:
	- find . -type d -name "__pycache__" -exec rm -r {} +
	- find . -type f -name "*.pyc" -delete
	- find . -type f -name ".coverage*" -delete
	- find . -type f -name "coverage.xml" -delete
	- find . -type d -name ".pytest_cache" -exec rm -rf {} +
	- find . -type d -name "htmlcov" -exec rm -rf {} +
	- find . -type d -name "jira_creator.egg-info" -exec rm -rf {} +
	- find . -type d -name "dist" -exec rm -rf {} +
	- rm -rvf log.log
	- rm -rvf d_fake_seeder/log.log
	- rm -rvf dist
	- rm -rvf .pytest_cache
	- find . -type d -iname __pycache__ -exec rm -rf {} \;
	- rm -rvf debbuild
	- rm -rvf rpmbuild
	- rm -rvf *.deb
	- rm -rvf *.rpm

rpm: clean
	- sudo dnf install -y rpm-build rpmlint python3-setuptools python3-setuptools
	rm -rvf ./rpmbuild
	mkdir -p ./rpmbuild/BUILD ./rpmbuild/BUILDROOT ./rpmbuild/RPMS ./rpmbuild/SOURCES ./rpmbuild/SPECS ./rpmbuild/SRPMS ./rpmbuild/SOURCE
	cp -r jira-creator.spec ./rpmbuild/SPECS/
	cp -r jira_creator/rh_jira.py ./rpmbuild/SOURCE/
	tar -czvf rpmbuild/SOURCES/$(RPM_FILENAME).tar.gz jira_creator/ 
	rpmbuild --define "_topdir `pwd`/rpmbuild" -v -ba ./rpmbuild/SPECS/jira-creator.spec

rpm-install: rpm
	sudo dnf install rpmbuild/RPMS/<architecture>/python-example-1.0-1.<architecture>.rpm
	rpmlint

deb: clean
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

deb-install: deb	
	sudo dpkg -i $(DEB_FILENAME)

super-lint: $(SUPER_LINTER_CONFIGS)
	docker run --rm \
	-e SUPER_LINTER_LINTER=error \
	-e LINTER_OUTPUT=error \
	-e LOG_LEVEL=ERROR \
	-e RUN_LOCAL=true \
	-e FILTER_REGEX_EXCLUDE="(^|/)\.git(/|$)" \
	-e GIT_IGNORE=true \
	-v $$(pwd):/tmp/lint \
	github/super-linter:latest --quiet

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

.PHONY: weaviate-setup
weaviate-setup:
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
	@echo "  make format      - Auto-format code"
	@echo "  make clean       - Remove __pycache__ and *.pyc files"
