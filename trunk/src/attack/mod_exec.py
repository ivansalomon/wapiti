from attack import Attack
from vulnerability import Vulnerability
from vulnerabilitiesdescriptions import VulnerabilitiesDescriptions as VulDescrip
import requests
from net import HTTP

# Wapiti SVN - A web application vulnerability scanner
# Wapiti Project (http://wapiti.sourceforge.net)
# Copyright (C) 2008 Nicolas Surribas
#
# David del Pozo
# Alberto Pastor
# Informatica Gesfor
# ICT Romulus (http://www.ict-romulus.eu)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

class mod_exec(Attack):
    """
    This class implements a command execution attack
    """

    CONFIG_FILE = "execPayloads.txt"

    name = "exec"

    def __init__(self, HTTP, xmlRepGenerator):
        Attack.__init__(self, HTTP, xmlRepGenerator)
        self.payloads = self.loadPayloads(self.CONFIG_DIR + "/" + self.CONFIG_FILE)

    def __findPatternInResponse(self, data, warned):
        err = ""
        cmd = 0
        if "eval()'d code</b> on line <b>" in data and not warned:
            err = "Warning eval()"
            warned = 1
        if "PATH=" in data and "PWD=" in data:
            err = _("Command execution")
            cmd = 1
        if "w4p1t1_eval" in data:
            err = _("PHP evaluation")
            cmd = 1
        if "Cannot execute a blank command in" in data and not warned:
            err = "Warning exec"
            warned = 1
        if "sh: command substitution:" in data and not warned:
            err = "Warning exec"
            warned = 1
        if "Fatal error</b>:  preg_replace" in data and not warned:
            err = _("preg_replace injection")
            warned = 1
        return err, cmd, warned

    def attackGET(self, http_res):
        """This method performs the command execution with method GET"""

        page = http_res.path
        params_list = http_res.get_params
        resp_headers = http_res.headers
        referer = http_res.referer
        headers = {}
        if referer:
            headers["referer"] = referer

        if not params_list:
            # Do not attack application-type files
            if not "content-type" in resp_headers:
                # Sometimes there's no content-type... so we rely on the document extension
                if (page.split(".")[-1] not in self.allowed) and page[-1] != "/":
                    return
            elif not "text" in resp_headers["content-type"]:
                return

            warned = 0
            cmd = 0
            err500 = 0

            for payload in self.payloads:
                err = ""
                url = page + "?" + self.HTTP.quote(payload)

                if url not in self.attackedGET:
                    evil_req = HTTP.HTTPResource(url)
                    if self.verbose == 2:
                        print "+", url
                    self.attackedGET.append(url)
                    try:
                        data, code = self.HTTP.send(evil_req, headers=headers).getPageCode()
                    except requests.exceptions.Timeout, timeout:
                        data = ""
                        code = "408"
                        err = ""
                        print _("Timeout in"), page
                        print "  " + _("caused by") + ":", evil_req.url
                        self.logVuln(category=Vulnerability.RES_CONSUMPTION,
                                     level=Vulnerability.MEDIUM_LEVEL_VULNERABILITY,
                                     request=evil_req,
                                     info=err + " " + _("(QUERY_STRING)"))
                    else: 
                        err, cmd, warned = self.__findPatternInResponse(data, warned)
                    if err != "":
                        self.logVuln(category=Vulnerability.EXEC,
                                     level=Vulnerability.HIGH_LEVEL_VULNERABILITY,
                                     request=evil_req,
                                     info=err + " " + _("(QUERY_STRING)"))
                        print err, _("(QUERY_STRING) in"), page
                        print "  " + _("Evil url") + ":", evil_req.url
                    else:
                        if code == "500" and err500 == 0:
                            err500 = 1
                            self.logVuln(category=Vulnerability.EXEC,
                                         level=Vulnerability.HIGH_LEVEL_VULNERABILITY,
                                         request=evil_req,
                                         info=VulDescrip.ERROR_500 + "\n" + VulDescrip.ERROR_500_DESCRIPTION)
                            print _("500 HTTP Error code with")
                            print "  " + _("Evil url") + ":", evil_req.url
                    if cmd:
                        break

        for i in range(len(params_list)):
            warned = 0
            cmd = 0
            err500 = 0

            saved_value = params_list[i][1]
            params_list[i][1] = "__EXEC__"
            url = page + "?" + self.HTTP.encode(params_list)
            param_name = self.HTTP.quote(params_list[i][0])

            if url not in self.attackedGET:
                self.attackedGET.append(url)

                for payload in self.payloads:
                    err = ""
                    params_list[i][1] = self.HTTP.quote(payload)
                    evil_req = HTTP.HTTPResource(page + "?" + self.HTTP.encode(params_list))

                    if self.verbose == 2:
                        print "+", evil_req.url

                    try:
                        data, code = self.HTTP.send(evil_req.url, headers=headers).getPageCode()
                    except requests.exceptions.Timeout, timeout:
                        data = ""
                        code = "408"
                        err = ""
                        print _("Timeout") + " (" + param_name + ") " + _("in"), page
                        print "  " + _("caused by") + ":", evil_req.url
                        self.logVuln(category=Vulnerability.RES_CONSUMPTION,
                                     level=Vulnerability.MEDIUM_LEVEL_VULNERABILITY,
                                     request=evil_req,
                                     parameter=param_name,
                                     info=err + " (" + param_name + ")")
                    else:
                        err, cmd, warned = self.__findPatternInResponse(data, warned)
                    if err != "":
                        self.logVuln(category=Vulnerability.EXEC,
                                     level=Vulnerability.HIGH_LEVEL_VULNERABILITY,
                                     request=evil_req,
                                     parameter=param_name,
                                     info=err + " (" + param_name + ")")
                        if self.color == 0:
                            print err, "(" + param_name + ") " + _("in"), page
                            print "  " + _("Evil url") + ":", evil_req.url
                        else:
                            print err, ":", evil_req.url.replace(param_name + "=", self.RED + param_name + self.STD + "=")

                        if cmd:
                            # Successful command execution, go to the next field
                            break
                    else:
                        if code == "500" and err500 == 0:
                            err500 = 1
                            self.logVuln(category=Vulnerability.EXEC,
                                         level=Vulnerability.HIGH_LEVEL_VULNERABILITY,
                                         request=evil_req,
                                         parameter=param_name,
                                         info=VulDescrip.ERROR_500 + "\n" + VulDescrip.ERROR_500_DESCRIPTION)
                            print _("500 HTTP Error code with")
                            print "  " + _("Evil url") + ":", evil_req.url
            params_list[i][1] = saved_value

    def attackPOST(self, form):
        """This method performs the command execution with method POST"""

        # copies
        get_params = form.get_params
        post_params = form.post_params
        file_params = form.file_params
        referer = form.referer

        for param_list in [get_params, post_params, file_params]:
            for i in xrange(len(param_list)):
                saved_value = param_list[i][1]
                warned = 0
                cmd = 0
                err500 = 0
                param_name = self.HTTP.quote(param_list[i][0])
                param_list[i][1] = "__EXEC__"
                attack_pattern = HTTP.HTTPResource(form.path, method=form.method, get_params=get_params, post_params=post_params, file_params=file_params)
                if attack_pattern not in self.attackedPOST:
                    self.attackedPOST.append(attack_pattern)
                    for payload in self.payloads:
                        # no quoting: send() will do it for us
                        param_list[i][1] = payload
                        evil_req = HTTP.HTTPResource(form.path,
                                                     method=form.method,
                                                     get_params=get_params,
                                                     post_params=post_params,
                                                     file_params=file_params,
                                                     referer=referer)
                        if self.verbose == 2:
                            print "+", evil_req
                        err = ""
                        try:
                            data, code = self.HTTP.send(evil_req).getPageCode()
                        except requests.exceptions.Timeout, timeout:
                            data = ""
                            code = "408"
                            print _("Timeout in"), evil_req.url
                            print "  " + _("with params") + " =", self.HTTP.encode(post_params)
                            print "  " + _("coming from"), referer
                            self.logVuln(category=Vulnerability.RES_CONSUMPTION,
                                         level=Vulnerability.MEDIUM_LEVEL_VULNERABILITY,
                                         request=evil_req,
                                         parameter=param_name,
                                         info=_("Timeout coming from") + " " + referer)
                        else:
                            err, cmd, warned = self.__findPatternInResponse(data, warned)

                        if err != "":
                            self.logVuln(category=Vulnerability.EXEC,
                                         level=Vulnerability.HIGH_LEVEL_VULNERABILITY,
                                         request=evil_req,
                                         parameter=param_name,
                                         info=err + " " + _("coming from") + " " + referer)
                            print err, _("in"), evil_req.url
                            if self.color == 1:
                                print "  " + _("with params") + " =", \
                                        self.HTTP.encode(post_params).replace(param_name + "=", self.RED + param_name + self.STD + "=")
                            else:
                                print "  " + _("with params") + " =", self.HTTP.encode(post_params)
                            print "  " + _("coming from"), referer
                            if cmd:
                                # Successful command execution, go to the next field
                                break

                        else:
                            if code == "500" and err500 == 0:
                                err500 = 1
                                self.logVuln(category=Vulnerability.EXEC,
                                            level=Vulnerability.HIGH_LEVEL_VULNERABILITY,
                                            request=evil_req,
                                             parameter=param_name,
                                            info=_("500 HTTP Error code coming from") + " " + referer + "\n" + \
                                                 VulDescrip.ERROR_500_DESCRIPTION)
                                print _("500 HTTP Error code in"), evil_req.url
                                print "  " + _("with params") + " =", self.HTTP.encode(post_params)
                                print "  " + _("coming from"), referer
                param_list[i][1] = saved_value



