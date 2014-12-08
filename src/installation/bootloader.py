#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  bootloader.py
#
#  Copyright © 2013,2014 Antergos
#
#  This file is part of Cnchi.
#
#  Cnchi is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  Cnchi is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Cnchi; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

import logging
import os
import shutil
import parted3.fs_module as fs

class Bootloader(object):
    def __init__(self, dest_dir, settings, mount_devices)
        self.dest_dir = dest_dir
        self.settings = settings
        self.mount_devices = mount_devices

    def install(self):
        """ Installs the bootloader """

        # Freeze and unfreeze xfs filesystems to enable bootloader installation on xfs filesystems
        freeze_unfreeze_xfs()

        bootloader = self.settings.get('bootloader').lower()
        if bootloader == "grub2":
            self.install_grub()
        elif bootloader == "gummiboot":
            self.install_bootloader_gummiboot()

    def install_grub(self):
        self.modify_grub_default()
        self.prepare_grub_d()

        if os.path.exists('/sys/firmware/efi'):
            self.install_grub2_efi()
        else:
            self.install_grub2_bios()

        # Check grub.cfg for correct root UUID (just in case)
        cfg = os.path.join(self.dest_dir, "boot/grub/grub.cfg")
        ruuid = self.settings.get('ruuid')
        ruuid_ok = False

        with open(cfg) as grub_cfg:
            if ruuid in grub_cfg.read():
                ruuid_ok = True

        if not ruuid_ok:
            # Wrong uuid in grub.cfg, let's fix it!
            with open(cfg) as grub_cfg:
                lines = [x.strip() for x in grub_cfg.readlines()]
            for i in range(len(lines)):
                if lines[i].startswith("linux") and "/vmlinuz-linux root=" in lines[i]:
                    old_line = lines[i]
                    p1 = old_line[68:]
                    p2 = old_line[:26]
                    lines[i] = p1 + ruuid + p2
            with open(cfg, 'w') as grub_cfg:
                grub_cfg.write("\n".join(lines))

    def modify_grub_default(self):
        """ If using LUKS as root, we need to modify GRUB_CMDLINE_LINUX """

        default_dir = os.path.join(self.dest_dir, "etc/default")
        default_grub = os.path.join(default_dir, "grub")
        theme = 'GRUB_THEME="/boot/grub/themes/Antergos-Default/theme.txt"'
        plymouth_bin = os.path.join(self.dest_dir, "usr/bin/plymouth")
        if os.path.exists(plymouth_bin):
            use_splash = 'splash'
        else:
            use_splash = ''

        if "swap" in self.mount_devices:
            swap_partition = self.mount_devices["swap"]
            swap_uuid = fs.get_info(swap_partition)['UUID']
            kernel_cmd = 'GRUB_CMDLINE_LINUX_DEFAULT="resume=UUID=%s quiet %s"' % (swap_uuid, use_splash)
        else:
            kernel_cmd = 'GRUB_CMDLINE_LINUX_DEFAULT="quiet %s"' % use_splash

        if not os.path.exists(default_dir):
            os.mkdir(default_dir)

        with open(default_grub) as grub_file:
            lines = [x.strip() for x in grub_file.readlines()]

        if self.settings.get('use_luks'):
            boot_device = self.mount_devices["/boot"]
            boot_uuid = fs.get_info(boot_device)['UUID']

            # Let GRUB automatically add the kernel parameters for root encryption
            luks_root_volume = self.settings.get('luks_root_volume')

            logging.debug("Luks Root Volume: %s", luks_root_volume)

            if self.method == "advanced" and self.settings.get('use_luks_in_root'):
                root_device = self.settings.get('luks_root_device')
            elif self.method == "automatic":
                root_device = self.mount_devices["/"]

            logging.debug("Root device: %s", root_device)

            root_uuid = fs.get_info(root_device)['UUID']

            if self.settings.get("luks_root_password") == "":
                default_line = 'GRUB_CMDLINE_LINUX="cryptdevice=/dev/disk/by-uuid/%s:%s ' \
                            'cryptkey=/dev/disk/by-uuid/%s:ext2:/.keyfile-root"' % (root_uuid, luks_root_volume, boot_uuid)
            else:
                default_line = 'GRUB_CMDLINE_LINUX="cryptdevice=/dev/disk/by-uuid/%s:%s"' % (root_uuid, luks_root_volume)

            for i in range(len(lines)):
                if lines[i].startswith("#GRUB_CMDLINE_LINUX") or lines[i].startswith("GRUB_CMDLINE_LINUX"):
                    if not lines[i].startswith("#GRUB_CMDLINE_LINUX_DEFAULT"):
                        if not lines[i].startswith("GRUB_CMDLINE_LINUX_DEFAULT"):
                            lines[i] = default_line

        for i in range(len(lines)):
            if lines[i].startswith("#GRUB_THEME") or lines[i].startswith("GRUB_THEME"):
                lines[i] = theme
            elif lines[i].startswith("#GRUB_CMDLINE_LINUX_DEFAULT") or lines[i].startswith("GRUB_CMDLINE_LINUX_DEFAULT"):
                lines[i] = kernel_cmd
            elif lines[i].startswith("#GRUB_DISTRIBUTOR") or lines[i].startswith("GRUB_DISTRIBUTOR"):
                lines[i] = "GRUB_DISTRIBUTOR=Antergos"

        with open(default_grub, 'w') as grub_file:
            grub_file.write("\n".join(lines) + "\n")

        logging.debug(_("/etc/default/grub configuration completed successfully."))

    def prepare_grub_d(self):
        """ Copies 01_antergos script into /etc/grub.d. """
        grub_d_dir = os.path.join(self.dest_dir, "etc/grub.d")
        script_dir = os.path.join(self.settings.get("cnchi"), "scripts")
        script = "10_antergos"

        if not os.path.exists(grub_d_dir):
            os.makedirs(grub_d_dir)

        try:
            shutil.copy2(os.path.join(script_dir, script), grub_d_dir)
            os.chmod(os.path.join(grub_d_dir, script), 0o755)
        except FileNotFoundError:
            logging.debug(_("Could not copy %s to grub.d"), script)
        except FileExistsError:
            pass

    def install_grub2_bios(self):
        """ Install Grub2 bootloader in a BIOS system """
        grub_location = self.settings.get('bootloader_device')
        txt = _("Installing GRUB(2) BIOS boot loader in %s") % grub_location
        self.queue_event('info', txt)

        self.chroot_mount_special_dirs()

        grub_install = ['grub-install', '--directory=/usr/lib/grub/i386-pc', '--target=i386-pc',
                        '--boot-directory=/boot', '--recheck']

        if len(grub_location) > 8:  # ex: /dev/sdXY > 8
            grub_install.append("--force")

        grub_install.append(grub_location)

        self.chroot(grub_install)

        self.install_grub2_locales()

        self.copy_grub2_theme_files()

        # Run grub-mkconfig last
        locale = self.settings.get("locale")
        try:
            self.chroot(['sh', '-c', 'LANG=%s grub-mkconfig -o /boot/grub/grub.cfg' % locale], 45)
        except subprocess.TimeoutExpired:
            logging.error(_("grub-mkconfig appears to be hung. Killing grub-mount and os-prober so we can continue."))
            subprocess.check_call(['killall', 'grub-mount'])
            subprocess.check_call(['killall', 'os-prober'])

        self.chroot_umount_special_dirs()

        cfg = os.path.join(self.dest_dir, "boot/grub/grub.cfg")
        with open(cfg) as grub_cfg:
            if "Antergos" in grub_cfg.read():
                self.queue_event('info', _("GRUB(2) BIOS has been successfully installed."))
                self.settings.set('bootloader_installation_successful', True)
            else:
                logging.warning(_("ERROR installing GRUB(2) BIOS."))
                self.settings.set('bootloader_installation_successful', False)

    def install_grub2_efi(self):
        """ Install Grub2 bootloader in a UEFI system """
        uefi_arch = "x86_64"
        spec_uefi_arch = "x64"
        spec_uefi_arch_caps = "X64"

        txt = _("Installing GRUB(2) UEFI %s boot loader") % uefi_arch
        self.queue_event('info', txt)

        grub_install = ['grub-install', '--target=%s-efi' % uefi_arch, '--efi-directory=/install/boot',
            '--bootloader-id=antergos_grub', '--boot-directory=/install/boot', '--recheck']
        try:
            subprocess.check_call(grub_install, shell=True, timeout=45)
        except subprocess.CalledProcessError as err:
            logging.error('Command grub-install failed. Error output: %s' % err.output)
        except subprocess.TimeoutExpired:
            logging.error('Command grub-install timed out.')
        except Exception as err:
            logging.error('Command grub-install failed. Unknown Error: %s' % err)

        self.install_grub2_locales()

        self.copy_grub2_theme_files()

        # Copy grub into dirs known to be used as default by some OEMs if they do not exist yet.
        defaults = [(os.path.join(self.dest_dir, "boot/EFI/BOOT/"), 'BOOT' + spec_uefi_arch_caps + '.efi'),
                    (os.path.join(self.dest_dir, "boot/EFI/Microsoft/Boot/"), 'bootmgfw.efi')]
        grub_dir_src = os.path.join(self.dest_dir, "boot/EFI/antergos_grub/")
        grub_efi_old = ('grub' + spec_uefi_arch + '.efi')

        for default in defaults:
            path, grub_efi_new = default
            if not os.path.exists(path):
                msg = _("No OEM loader found in %s. Copying Grub(2) into dir.") % path
                self.queue_event('info', msg)
                os.makedirs(path)
                msg_failed = _("Copying Grub(2) into OEM dir failed: ")
                try:
                    shutil.copy(grub_dir_src + grub_efi_old, path + grub_efi_new)
                except FileNotFoundError:
                    msg_failed = msg_failed + _("File Not Found.")
                    logging.warning(msg_failed)
                except FileExistsError:
                    msg_failed = msg_failed + _("File already exists.")
                    logging.warning(msg_failed)
                except Exception as err:
                    msg_failed = msg_failed + _("Unknown error.")
                    logging.warning(msg_failed)

        # Copy uefi shell if none exists in /boot/EFI
        shell_src = "/usr/share/cnchi/grub2-theme/shellx64_v2.efi"
        shell_dst = os.path.join(self.dest_dir, "boot/EFI/")
        try:
            shutil.copy2(shell_src, shell_dst)
        except FileNotFoundError:
            logging.warning(_("UEFI Shell drop-in not found at %s"), shell_src)
        except FileExistsError:
            pass
        except Exception as err:
            logging.warning(_("UEFI Shell drop-in could not be copied."))
            logging.warning(err)

        # Run grub-mkconfig last
        self.queue_event('info', _("Generating grub.cfg"))
        self.chroot_mount_special_dirs()

        locale = self.settings.get("locale")

        try:
            self.chroot(['sh', '-c', 'LANG=%s grub-mkconfig -o /boot/grub/grub.cfg' % locale], 45)
        except subprocess.TimeoutExpired:
            logging.error(_("grub-mkconfig appears to be hung. Killing grub-mount and os-prober so we can continue."))
            subprocess.check_call(['killall', 'grub-mount'])
            subprocess.check_call(['killall', 'os-prober'])

        self.chroot_umount_special_dirs()

        path = (
            (os.path.join(self.dest_dir, "boot/grub/x86_64-efi/core.efi")),
            (os.path.join(self.dest_dir, ("boot/EFI/antergos_grub/" + grub_efi_old))))

        exists = []

        for p in path:
            if os.path.exists(p):
                exists.append(p)

        if len(exists) == 0:
            logging.warning(_("GRUB(2) UEFI install may not have completed successfully."))
            self.settings.set('bootloader_installation_successful', False)
        else:
            self.queue_event('info', _("GRUB(2) UEFI install completed successfully"))
            self.settings.set('bootloader_installation_successful', True)

    def copy_grub2_theme_files(self):
        """ Copy grub2 theme files to /boot """
        self.queue_event('info', _("Copying GRUB(2) Theme Files"))
        theme_dir_src = "/usr/share/cnchi/grub2-theme/Antergos-Default"
        theme_dir_dst = os.path.join(self.dest_dir, "boot/grub/themes/Antergos-Default")
        try:
            shutil.copytree(theme_dir_src, theme_dir_dst)
        except FileNotFoundError:
            logging.warning(_("Grub2 theme files not found"))
        except FileExistsError:
            logging.warning(_("Grub2 theme files already exist."))

    def install_grub2_locales(self):
        """ Install Grub2 locales """
        self.queue_event('info', _("Installing Grub2 locales."))
        dest_locale_dir = os.path.join(self.dest_dir, "boot/grub/locale")

        if not os.path.exists(dest_locale_dir):
            os.makedirs(dest_locale_dir)

        grub_mo = os.path.join(self.dest_dir, "usr/share/locale/en@quot/LC_MESSAGES/grub.mo")

        try:
            shutil.copy2(grub_mo, os.path.join(dest_locale_dir, "en.mo"))
        except FileNotFoundError:
            logging.warning(_("Can't install GRUB(2) locale."))
        except FileExistsError:
            # Ignore if already exists
            pass

    def install_gummiboot(self):
        """ Install Gummiboot bootloader to the EFI System Partition """
        # Setup bootloader menu
        menu_dir = os.path.join(self.dest_dir, "boot/loader")
        os.makedirs(menu_dir)
        menu_path = os.path.join(menu_dir, "loader.conf")
        with open(menu_path, "w") as menu_file:
            menu_file.write("default antergos")

        # Setup boot entries
        entries_dir = os.path.join(self.dest_dir, "boot/loader/entries")
        os.makedirs(entries_dir)
        entry_path = os.path.join(entries_dir, "antergos.conf")
        with open(entry_path, "w") as entry_file:
            if not self.settings.get('use_luks'):
                root_device = self.mount_devices["/"]
                root_uuid = fs.get_info(root_device)['UUID']
                entry_file.write("title\tAntergos\n")
                entry_file.write("linux\t/vmlinuz-linux\n")
                entry_file.write("initrd\t/initramfs-linux.img\n")
                entry_file.write("options\troot=UUID=%s rw\n\n" % root_uuid)

                entry_file.write("title\tAntergos (fallback)\n")
                entry_file.write("linux\t/vmlinuz-linux\n")
                entry_file.write("initrd\t/initramfs-linux-fallback.img\n")
                entry_file.write("options\troot=UUID=%s rw\n\n" % root_uuid)

                if self.settings.get('feature_lts'):
                    entry_file.write("title\tAntergos LTS\n")
                    entry_file.write("linux\t/vmlinuz-linux-lts\n")
                    entry_file.write("initrd\t/initramfs-linux-lts.img\n")
                    entry_file.write("options\troot=UUID=%s rw\n\n" % root_uuid)

                    entry_file.write("title\tAntergos LTS (fallback)\n\n")
                    entry_file.write("linux\t/vmlinuz-linux-lts\n")
                    entry_file.write("initrd\t/initramfs-linux-lts-fallback.img\n")
                    entry_file.write("options\troot=UUID=%s rw\n" % root_uuid)
            else:
                boot_device = self.mount_devices["/boot"]
                boot_uuid = fs.get_info(boot_device)['UUID']
                luks_root_volume = self.settings.get('luks_root_volume')
                if self.method == "advanced" and self.settings.get('use_luks_in_root'):
                    root_device = self.settings.get('luks_root_device')
                elif self.method == "automatic":
                    root_device = self.mount_devices["/"]
                root_uuid = fs.get_info(root_device)['UUID']
                key = ""
                if self.settings.get("luks_root_password") == "":
                    key = "cryptkey=UUID=%s:ext2:/.keyfile-root" % boot_uuid

                line = "cryptdevice=UUID=%s:%s %s root=UUID=%s rw" % (root_uuid, luks_root_volume, key, root_uuid)

                entry_file.write("title\tAntergos\n")
                entry_file.write("linux\t/boot/vmlinuz-linux\n")
                entry_file.write("options\tinitrd=/boot/initramfs-linux.img %s\n\n" % line)

                entry_file.write("title\tAntergos (fallback)\n")
                entry_file.write("linux\t/boot/vmlinuz-linux\n")
                entry_file.write("options\tinitrd=/boot/initramfs-linux-fallback.img %s\n\n" % line)

                if self.settings.get('feature_lts'):
                    entry_file.write("title\tAntergos LTS\n")
                    entry_file.write("linux\t/boot/vmlinuz-linux-lts\n")
                    entry_file.write("options\tinitrd=/boot/initramfs-linux-lts.img %s\n\n" % line)

                    entry_file.write("title\tAntergos LTS (fallback)\n")
                    entry_file.write("linux\t/boot/vmlinuz-linux-lts\n")
                    entry_file.write("options\tinitrd=/boot/initramfs-linux-lts-fallback.img %s\n\n" % line)

        # Install bootloader

        try:
            efi_system_partition = os.path.join(self.dest_dir, "boot")
            subprocess.check_call(['gummiboot', '--path=%s' % efi_system_partition, 'install'])
            self.queue_event('info', _("Gummiboot install completed successfully"))
            self.settings.set('bootloader_installation_successful', True)
        except subprocess.CalledProcessError as err:
            logging.warning(_("Gummiboot install may not have completed successfully."))
            self.settings.set('bootloader_installation_successful', False)

    def freeze_unfreeze_xfs(self):
        """ Freeze and unfreeze xfs, as hack for grub(2) installing """
        if not os.path.exists("/usr/bin/xfs_freeze"):
            return

        xfs_boot = False
        xfs_root = False

        try:
            subprocess.check_call(["sync"])
            with open("/proc/mounts", "r") as mounts_file:
                mounts = mounts_file.readlines()
            # We leave a blank space in the end as we want to search exactly for this mount points
            boot_mount_point = self.dest_dir + "/boot "
            root_mount_point = self.dest_dir + " "
            for line in mounts:
                if " xfs " in line:
                    if boot_mount_point in line:
                        xfs_boot = True
                    elif root_mount_point in line:
                        xfs_root = True
            if xfs_boot:
                boot_mount_point = boot_mount_point.rstrip()
                subprocess.check_call(["xfs_freeze", "-f", boot_mount_point])
                subprocess.check_call(["xfs_freeze", "-u", boot_mount_point])
            if xfs_root:
                subprocess.check_call(["xfs_freeze", "-f", self.dest_dir])
                subprocess.check_call(["xfs_freeze", "-u", self.dest_dir])
        except subprocess.CalledProcessError as err:
            logging.warning(_("Can't freeze/unfreeze xfs system"))
