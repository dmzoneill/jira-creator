# --- Variables ---
deb_package_name := $(shell cat control | grep Package | sed 's/Package: //')
rpm_package_name := $(shell cat jira-creator.spec | grep Name | cut -d: -f 2 | tr -d ' ')
package_version := $(shell cat control | grep Version | sed 's/Version: //')
DEB_FILENAME := $(deb_package_name)_$(package_version).deb
RPM_FILENAME := $(rpm_package_name)-$(package_version)

PYTHON ?= python
PIPENV ?= pipenv
SCRIPT := rh-jira.py

# --- Setup & Install ---
.PHONY: install
install:
	$(PIPENV) install --dev

.PHONY: setup
setup: install
	@echo "✅ Virtualenv and dependencies ready."

# --- Run Script ---
.PHONY: run
run:
	$(PIPENV) run $(PYTHON) $(SCRIPT)

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
	echo "OPENAI_API_KEY=NOT_A_SECRET" >> $$GITHUB_ENV
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
	pipenv run autopep8 . --recursive --in-place --aggressive --aggressive
	pipenv run black .

# Run tests with coverage, including subprocess tracking
.PHONY: coverage
coverage:
	pipenv run coverage erase
	PYTHONPATH=.:jira_creator COVERAGE_PROCESS_START=.coveragerc pipenv run coverage run -m pytest jira_creator/tests
	pipenv run coverage combine
	pipenv run coverage report -m --fail-under=99
	pipenv run coverage html
	@echo "📂 Coverage report: open htmlcov/index.html"


# Clean up coverage artifacts
clean-coverage:
	rm -rf .coverage htmlcov

# --- Clean ---
.PHONY: clean
clean:
	- find . -type d -name "__pycache__" -exec rm -r {} +
	- find . -type f -name "*.pyc" -delete
	- find . -type f -name ".coverage" -delete
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
	mkdir -p ./rpmbuild/BUILD ./rpmbuild/BUILDROOT ./rpmbuild/RPMS ./rpmbuild/SOURCES ./rpmbuild/SPECS ./rpmbuild/SRPMS
	cp -r jira-creator.spec ./rpmbuild/SPECS/
	cp -r jira_creator/images ./rpmbuild/SOURCE/
	cp -r jira_creator/lib ./rpmbuild/SOURCE/
	cp -r jira_creator/ui ./rpmbuild/SOURCE/
	cp -r jira_creator/dfakeseeder.py ./rpmbuild/SOURCE/
	cp -r jira_creator/dfakeseeder.desktop ./rpmbuild/SOURCE/
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

	sudo chown -R root:root debbuild
	fakeroot dpkg-deb --build debbuild $(DEB_FILENAME)

	dpkg -c $(DEB_FILENAME)
	dpkg -I $(DEB_FILENAME)

deb-install: deb	
	sudo dpkg -i $(DEB_FILENAME)

# --- Help ---
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make install     - Install dependencies"
	@echo "  make setup       - Setup the environment"
	@echo "  make run         - Run the script"
	@echo "  make dry-run     - Run script in dry-run mode"
	@echo "  make test        - Run all unit tests"
	@echo "  make lint        - Run format checks"
	@echo "  make format      - Auto-format code"
	@echo "  make clean       - Remove __pycache__ and *.pyc files"
