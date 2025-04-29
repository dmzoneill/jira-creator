Name: JiraCreator
Version:    0.0.42
Release:    1%{?dist}
Summary:    Jira Cli App

License:    GPL
URL:        https://github.com/dmzoneill/jira-creator

Source0:    %{name}-%{version}.tar.gz

%description
Managing jira in work

%prep

%install
# Install files to desired locations
install -d %{buildroot}/opt/jira_creator/
cp -r ../SOURCE/* %{buildroot}/opt/jira_creator/
mkdir -vp %{buildroot}/usr/share/applications/

%files
%defattr(-,root,root,-)
/opt/jira_creator/*

%post
# Copy files to desired locations
echo "All done"