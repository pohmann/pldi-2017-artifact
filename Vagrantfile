Vagrant.configure(2) do |config|

  config.vm.box = "fedora/25-cloud-base"

  config.vm.provider :virtualbox do |provider|
    provider.cpus = `nproc`.to_i / 2
    provider.customize ["modifyvm", :id, "--ostype", "Fedora_64"]
    provider.memory = 32768  # 32 GB
    provider.name = "PLDI 2017 artifact on Fedora 25"
  end

  config.vm.synced_folder ".", "/vagrant",
     rsync__exclude: [".svn", "modify-vagrant-virtualbox-disk", "*.vmdk"],
     rsync__args: ["--verbose", "--archive", "-z"]

  config.vm.provision "system package updates and additions",
                      type: "shell",
                      inline: <<-SHELL
    dnf --assumeyes --best --allowerasing update
    dnf --assumeyes install \
      automake \
      bison \
      flex \
      gcc-c++ \
      gdb \
      java-1.8.0-openjdk-devel \
      maven \
      openfst-1.5.4 \
      openfst-devel-1.5.4 \
      patch \
      perl-Pod-Html \
      popt-devel \
      python2-networkx \
      python2-pexpect \
      python3-pandas \
      python3-scipy \
      redhat-rpm-config \
      scons \
      tcsh \
      texinfo
  SHELL
  config.vm.provision :reload
  config.vbguest.auto_reboot = false
  config.vbguest.no_install = true

  config.vm.provision "other package dependencies",
                      type: "shell",
                      inline: <<-SHELL
    pip install JPype1
    pip install pyfst
    pip3 install tabulate
    echo "kernel/core_pattern = core" >> /etc/sysctl.conf
  SHELL

  config.vm.provision "user setup",
                      type: "shell",
                      privileged: false,
                      inline: <<-SHELL
    cd /vagrant
    make csi-grissom/stamp
    make csi-cc/stamp
    echo "export PATH=$PATH:/vagrant/csi-grissom:/vagrant/csi-grissom/analysis:/vagrant/csi-cc/Release" >> /home/vagrant/.bashrc
    echo "ulimit -c unlimited" >> /home/vagrant/.bashrc
  SHELL

end
