#!/usr/bin/env python3
import time
import sys
import pexpect
import subprocess
import argparse
IDRAC_CMD = '/opt/dell/srvadmin/sbin/racadm' # dell racadm tools dir


def deploy_iso(idrac_ip, idrac_user, idrac_password, logger_obj=print):
    '''
    DOCSTRING: Deploy build performs 5 steps:
    step 1: prepare idrac connection string to idrac
    step 2: excute vmdisconnect cmd on idrac try vmdisconnect twice, make sure the vm-media is disconnected
    step 3: excute enable_ipmionlan cmd on idrac
    step 4: set boot from vcd on idrac
    step 5: deploy iso, try 5 times
    '''
    idrac_prompt = f"{IDRAC_CMD} -r {idrac_ip} -u {idrac_user} -p {idrac_password}"

    subcmd_list = ['vmdisconnect', 'vmdisconnect',
                   'config -g cfgIpmiLan -o cfgIpmiLanEnable 1',
                   'config -g cfgServerInfo -o cfgServerBootOnce 1',
                   'config -g cfgServerInfo -o cfgServerFirstBootDevice vCD-DVD']

    logger_obj('Deploying build...')

    for subcmd in subcmd_list:
        cmdstr = f"{idrac_prompt} {subcmd}"
        logger_obj('CMD: ' + cmdstr)
        p = subprocess.Popen(cmdstr, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, shell=True)
        output, err_out = p.communicate()
        logger_obj(f'SUBSHELL: {output} {err_out}')
        time.sleep(3)

    atempts = 5
    idrac8_flg = 0
    REMOTE_HOST_USER = ('"' + '' + '"')
    REMOTE_HOST_PASSWORD = ('"' + '' + '"')
    for i in range(atempts):
        if idrac8_flg == 0:
            cmdstr = (f"{IDRAC_CMD} -r {idrac_ip} -u {idrac_user} \
            -p {idrac_password} remoteimage -c -l")
        else:
            cmdstr = (f'{IDRAC_CMD} -r {idrac_ip} -u {idrac_user} -p \
                      {idrac_password} remoteimage -c \
                      -u {REMOTE_HOST_USER} -p {REMOTE_HOST_PASSWORD} -l')
        logger_obj('Deploy : ' + cmdstr)

        t = subprocess.Popen(cmdstr, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, shell=True)
        output, err_out = t.communicate()
        logger_obj(f'DPLYSHELL:   {output} {err_out}')
        if str(output).find('Remote Image is now Configured') > 0:
        #if 'Remote Image is now Configured' in str(output):
            logger_obj('ISO deployment tasks started successfully, now mounted to IDRAC') #idrac 9
            break
        elif str(output).find('The -c option requires -u to also be specifed') > 0:
            logger_obj('IDRAC VERSION CMD CHANGE -u -p required') #idrac 8
            idrac8_flg = 1
            continue
        else:
            logger_obj('iso deployment tasks started but failed, try again.')
            util.kill_process('racadm -r %s' % idrac_ip)
            time.sleep(3)
            continue

    if i == atempts-1:
        logger_obj(f'ERROR: Deployment failed {atempts} times.')
        ret = 'DEPLOY_BUILD_ERR'
    else:
        logger_obj('Image deployment completed.')
        ret = 0

    time.sleep(60)

    return ret


def boot_iso(idrac_ip, idrac_user, idrac_password, logger_obj=print):
    '''
    DOCSTRING: install build, calls racadm with the powercycle action reboot the server to begin
    the install. An image should be mounted and set as server next boot device.
    '''
    logger_obj(' . . . Rebooting for OS install . . . ')

    pwrcmdstr = (f"{IDRAC_CMD} -r {idrac_ip} -u {idrac_user} -p {idrac_password} \
            serveraction powercycle")

    logger_obj('rebootCMD: ' + pwrcmdstr)
    subprocess.call(pwrcmdstr, stdout=subprocess.PIPE, shell=True)

    # define a wait period, or detect complete install
    return


def main(args, logger_obj=print):
    parser = argparse.ArgumentParser(args)
    parser.add_argument('ip', help='iDRAC management IP address')
    parser.add_argument('-u', help='IDRAC Console Username', required=True)
    parser.add_argument('-p', help='IDRAC Console Password', required=True)

    logger_obj('Installer Begin . . .')

    ret = deploy_iso(idrac_ip, idrac_user, idrac_password)
    if ret != 0:
        logger_obj('Deploy ISO failed')
        sys.exit(1)

    ret = boot_iso(idrac_ip, idrac_user, idrac_password)
    if ret != 0:
        logger_obj('Install Failed')
        sys.exit(1)

    logger_obj('ISO mount and reboot complete')


if __name__ == "__main__":
    main(sys.argv[1:])
