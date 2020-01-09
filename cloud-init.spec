%if 0%{?rhel} <= 5
%define __python /usr/bin/python2.6
%endif
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

# The only reason we are archful is because dmidecode is ExclusiveArch
# https://bugzilla.redhat.com/show_bug.cgi?id=1067089
%global debug_package %{nil}

Name:           cloud-init
Version:        0.7.5
Release:        8%{?dist}.2
Summary:        Cloud instance init scripts

Group:          System Environment/Base
License:        GPLv3
URL:            http://launchpad.net/cloud-init
Source0:        https://launchpad.net/cloud-init/trunk/%{version}/+download/%{name}-%{version}.tar.gz
Source1:        cloud-init-rhel.cfg
Source2:        cloud-init-README.rhel

Patch0001: 0001-packaging-configs-docs-and-path-changes-for-rhel.patch
Patch0002: 0002-fix-rsyslog-programname-match.patch
Patch0003: 0003-Stopped-calling-udevadm-settle-with-quiet-since-syst.patch
Patch0004: 0004-fix-typo-in-settings.py-preventing-metadata-being-fe.patch
Patch0005: 0005-hostname-apply-hostname-same-as-is-written.patch
Patch0006: 0006-set-correct-permissions-on-sshd_config.patch
Patch0007: 0007-Openstack-Vendor-data-cleanup.patch
Patch0008: 0008-Fix-slow-tests.patch
Patch0009: 0009-OpenStack-Use-timeout-and-retries-from-config-in-get.patch
Patch0010: 0010-AliYun-Add-new-datasource-for-Ali-Cloud-ECS.patch
Patch0011: 0011-DatasourceEc2-add-warning-message-when-not-on-AWS.patch
Patch0012: 0012-AliYun-Enable-platform-identification-and-enable-by-.patch
Patch0013: 0013-Drop-reliance-on-dmidecode-executable.patch
Patch0014: 0014-Fix-formatting-to-work-with-python-2.6.patch
Patch0015: 0015-Use-either-syspath-or-dmidecode-based-on-the-availab.patch
Patch0016: 0016-Convert-dmidecode-values-to-sysfs-names-before-looki.patch

BuildRequires:  python-devel
BuildRequires:  python-setuptools

%ifarch %{?ix86} x86_64 ia64
Requires:       dmidecode
%endif
Requires:       e2fsprogs
Requires:       iproute
Requires:       libselinux-python
Requires:       net-tools
Requires:       policycoreutils-python
Requires:       procps
Requires:       python-argparse
Requires:       python-boto
Requires:       python-cheetah
Requires:       python-configobj
Requires:       python-prettytable
Requires:       python-requests
Requires:       PyYAML
Requires:       python-jsonpatch
Requires:       shadow-utils
Requires:       /usr/bin/run-parts

%description
Cloud-init is a set of init scripts for cloud instances.  Cloud instances
need special scripts to run during initialization to retrieve and install
ssh keys and to let the user run various scripts.


%prep
%setup -q -n %{name}-%{version}

%patch0001 -p1
%patch0002 -p1
%patch0003 -p1
%patch0004 -p1
%patch0005 -p1
%patch0006 -p1
%patch0007 -p1
%patch0008 -p1
%patch0009 -p1
%patch0010 -p1
%patch0011 -p1
%patch0012 -p1
%patch0013 -p1
%patch0014 -p1
%patch0015 -p1
%patch0016 -p1

cp -p %{SOURCE2} README.rhel


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# Don't ship the tests
rm -r $RPM_BUILD_ROOT%{python_sitelib}/tests

mkdir -p $RPM_BUILD_ROOT/%{_sharedstatedir}/cloud

# We supply our own config file since our software differs from Ubuntu's.
cp -p %{SOURCE1} $RPM_BUILD_ROOT/%{_sysconfdir}/cloud/cloud.cfg

mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/rsyslog.d
cp -p tools/21-cloudinit.conf $RPM_BUILD_ROOT/%{_sysconfdir}/rsyslog.d/21-cloudinit.conf

# Install the init scripts
mkdir -p $RPM_BUILD_ROOT/%{_initrddir}
install -p -m 755 sysvinit/redhat/* $RPM_BUILD_ROOT/%{_initrddir}/

%clean
rm -rf $RPM_BUILD_ROOT


%post
if [ $1 -eq 1 ] ; then
    # Initial installation
    # Enabled by default per "runs once then goes away" exception
    for svc in init-local init config final; do
        chkconfig --add cloud-$svc
        chkconfig cloud-$svc on
    done
fi

%preun
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    for svc in init-local init config final; do
        chkconfig cloud-$svc off
        chkconfig --del cloud-$svc
    done
    # One-shot services -> no need to stop
fi

%postun
# One-shot services -> no need to restart


%files
%doc LICENSE
%doc ChangeLog TODO README.rhel
%config(noreplace) %{_sysconfdir}/cloud/cloud.cfg
%dir               %{_sysconfdir}/cloud/cloud.cfg.d
%config(noreplace) %{_sysconfdir}/cloud/cloud.cfg.d/*.cfg
%doc               %{_sysconfdir}/cloud/cloud.cfg.d/README
%dir               %{_sysconfdir}/cloud/templates
%config(noreplace) %{_sysconfdir}/cloud/templates/*
%{_initrddir}/cloud-*
%{python_sitelib}/*
%{_libexecdir}/%{name}
%{_bindir}/cloud-init*
%doc %{_datadir}/doc/%{name}
%dir %{_sharedstatedir}/cloud

%config(noreplace) %{_sysconfdir}/rsyslog.d/21-cloudinit.conf


%changelog
* Thu Oct 12 2017 Ryan McCabe <rmccabe@redhat.com> 0.7.5-8.2
- Pull in additional patches to support AliCloud
  Resolves: rhbz#1495471

* Tue Sep 26 2017 Ryan McCabe <rmccabe@redhat.com> 0.7.5-8.1
- Add support for the Alibaba cloud datasource (rhbz#1495471)

* Fri May 12 2017 Lars Kellogg-Stedman <lars@redhat.com> 0.7.5-8
- OpenStack: Use timeout and retries from config in get_data. (rhbz#1409951)

* Wed Apr 26 2017 Lars Kellogg-Stedman <lars@redhat.com> 0.7.5-7
- Openstack: Vendor data cleanup (rhbz#1437347)

* Mon Feb 20 2017 Charalampos Stratakis <cstratak@redhat.com> - 0.7.5-6
- Bump release for rebuild

* Fri Jan 08 2016 Lars Kellogg-Stedman <lars@redhat.com> 0.7.5-5
- remove rsyslog dependency (matches rhel7 package)

* Wed Jan 06 2016 Lars Kellogg-Stedman <lars@redhat.com> 0.7.5-4
- correct permissions on /etc/ssh/sshd_config [RH:1295984]

* Wed Feb 11 2015 Lars Kellogg-Stedman <lars@redhat.com> 0.7.5-3 (redhat)
- backport patch for https://bugs.launchpad.net/cloud-init/+bug/1246485
  (resolves rhbz#1191646)

* Thu Jan 22 2015 Lars Kellogg-Stedman <lars@redhat.com> 0.7.5-2 (redhat)
- added missing dependency on python-argparse (rhbz#1184826)

* Mon Jul 14 2014 Lars Kellogg-Stedman <lars@redhat.com> 0.7.5-1 (redhat)
- Rebased against upstream 0.7.5-6 in order to pull in GCE support.

* Thu Jun 12 2014 Dennis Gilmore <dennis@ausil.us> - 0.7.5-6
- fix typo in settings.py preventing metadata being fecthed in ec2

* Mon Jun  9 2014 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.5-5
- Stopped calling ``udevadm settle'' with --quiet since systemd 213 removed it

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.5-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Mon Jun  2 2014 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.5-3
- Make dmidecode dependency arch-dependent [RH:1025071 RH:1067089]

* Mon Jun  2 2014 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.2-9
- Write /etc/locale.conf instead of /etc/sysconfig/i18n [RH:1008250]
- Add tmpfiles.d configuration for /run/cloud-init [RH:1103761]
- Use the license rpm macro
- BuildRequire python-setuptools, not python-setuptools-devel

* Fri May 30 2014 Matthew Miller <mattdm@fedoraproject.org> - 0.7.5-2
- add missing python-jsonpatch dependency [RH:1103281]

* Tue Apr 29 2014 Sam Kottler <skottler@fedoraproject.org> - 0.7.5-1
- Update to 0.7.5 and remove patches which landed in the release

* Sat Jan 25 2014 Sam Kottler <skottler@fedoraproject.org> - 0.7.2-8
- Remove patch to the Puppet service unit name [RH:1057860]

* Tue Sep 24 2013 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.2-7
- Dropped xfsprogs dependency [RH:974329]

* Tue Sep 24 2013 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.2-6
- Added yum-add-repo module

* Fri Sep 20 2013 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.2-5
- Fixed puppet agent service name [RH:1008250]
- Let systemd handle console output [RH:977952 LP:1228434]
- Fixed restorecon failure when selinux is disabled [RH:967002 LP:1228441]
- Fixed rsyslog log filtering
- Added missing modules [RH:966888]

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Sat Jun 15 2013 Matthew Miller <mattdm@fedoraproject.org> - 0.7.2-3
- switch ec2-user to "fedora" --  see bugzilla #971439. To use another
  name, use #cloud-config option "users:" in userdata in cloud metadata
  service
- add that user to systemd-journal group

* Fri May 17 2013 Steven Hardy <shardy@redhat.com> - 0.7.2
- Update to the 0.7.2 release

* Thu May 02 2013 Steven Hardy <shardy@redhat.com> - 0.7.2-0.1.bzr809
- Rebased against upstream rev 809, fixes several F18 related issues
- Added dependency on python-requests

* Sat Apr  6 2013 Orion Poplawski <orion@cora.nwra.com> - 0.7.1-4
- Don't ship tests

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.7.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Thu Dec 13 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.1-2
- Added default_user to cloud.cfg (this is required for ssh keys to work)

* Wed Nov 21 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.1-1
- Rebased against version 0.7.1
- Fixed broken sudoers file generation
- Fixed "resize_root: noblock" [LP:1080985]

* Tue Oct  9 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.0-1
- Rebased against version 0.7.0
- Fixed / filesystem resizing

* Sat Sep 22 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.0-0.3.bzr659
- Added dmidecode dependency for DataSourceAltCloud

* Sat Sep 22 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.0-0.2.bzr659
- Rebased against upstream rev 659
- Fixed hostname persistence
- Fixed ssh key printing
- Fixed sudoers file permissions

* Mon Sep 17 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.7.0-0.1.bzr650
- Rebased against upstream rev 650
- Added support for useradd --selinux-user

* Thu Sep 13 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.3-0.5.bzr532
- Use a FQDN (instance-data.) for instance data URL fallback [RH:850916 LP:1040200]
- Shut off systemd timeouts [RH:836269]
- Send output to the console [RH:854654]

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.3-0.4.bzr532
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Wed Jun 27 2012 Pádraig Brady <P@draigBrady.com> - 0.6.3-0.3.bzr532
- Add support for installing yum packages

* Sat Mar 31 2012 Andy Grimm <agrimm@gmail.com> - 0.6.3-0.2.bzr532
- Fixed incorrect interpretation of relative path for
  AuthorizedKeysFile (BZ #735521)

* Mon Mar  5 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.3-0.1.bzr532
- Rebased against upstream rev 532
- Fixed runparts() incompatibility with Fedora

* Thu Jan 12 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.2-0.8.bzr457
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Wed Oct  5 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.7.bzr457
- Disabled SSH key-deleting on startup

* Wed Sep 28 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.6.bzr457
- Consolidated selinux file context patches
- Fixed cloud-init.service dependencies
- Updated sshkeytypes patch
- Dealt with differences from Ubuntu's sshd

* Sat Sep 24 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.5.bzr457
- Rebased against upstream rev 457
- Added missing dependencies

* Fri Sep 23 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.4.bzr450
- Added more macros to the spec file

* Fri Sep 23 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.3.bzr450
- Fixed logfile permission checking
- Fixed SSH key generation
- Fixed a bad method call in FQDN-guessing [LP:857891]
- Updated localefile patch
- Disabled the grub_dpkg module
- Fixed failures due to empty script dirs [LP:857926]

* Fri Sep 23 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.2.bzr450
- Updated tzsysconfig patch

* Wed Sep 21 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.1.bzr450
- Initial packaging
