import re
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


class mod_sql(Attack):
    """
    This class implements an SQL Injection attack
    """

    TIME_TO_SLEEP = 6
    name = "sql"

    def __init__(self, HTTP, xmlRepGenerator):
        Attack.__init__(self, HTTP, xmlRepGenerator)

    def __findPatternInResponse(self, data):
        if "You have an error in your SQL syntax" in data:
            return _("MySQL Injection")
        if "supplied argument is not a valid MySQL" in data:
            return _("MySQL Injection")
        if "[Microsoft][ODBC Microsoft Access Driver]" in data:
            return _("Access-Based SQL Injection")
        if "[Microsoft][ODBC SQL Server Driver]" in data:
            return _("MSSQL-Based Injection")
        if 'Microsoft OLE DB Provider for ODBC Drivers</font> <font size="2" face="Arial">error' in data:
            return _("MSSQL-Based Injection")
        if "Microsoft OLE DB Provider for ODBC Drivers" in data:
            return _("MSSQL-Based Injection")
        if "java.sql.SQLException: Syntax error or access violation" in data or \
           "java.sql.SQLException: Unexpected end of command" in data:
            return _("Java.SQL Injection")
        if "PostgreSQL query failed: ERROR: parser:" in data:
            return _("PostgreSQL Injection")
        if "XPathException" in data:
            return _("XPath Injection")
        if "supplied argument is not a valid ldap" in data or "javax.naming.NameNotFoundException" in data:
            return _("LDAP Injection")
        if "DB2 SQL error:" in data:
            return _("DB2 Injection")
        if "Dynamic SQL Error" in data:
            return _("Interbase Injection")
        if "Sybase message:" in data:
            return _("Sybase Injection")
        if "Unclosed quotation mark after the character string" in data:
            return _(".NET SQL Injection")

        #TODO: MS can also give some error codes like this: Microsoft SQL Native Client error '80040e14'
        ora_test = re.search("ORA-[0-9]{4,}", data)
        if ora_test is not None:
            return _("Oracle Injection") + " " + ora_test.group(0)

        return ""

    def setTimeout(self, timeout):
        self.TIME_TO_SLEEP = str(1 + int(timeout))

    def attackGET(self, http_res):
        """This method performs the SQL Injection attack with method GET"""
        page = http_res.path
        params_list = http_res.get_params
        resp_headers = http_res.headers
        referer = http_res.referer
        headers = {}
        if referer:
            headers["referer"] = referer

        # about this payload : http://shiflett.org/blog/2006/jan/addslashes-versus-mysql-real-escape-string
        payload = "\xBF'\"("
        vuln_found = 0

        if not params_list:
            # Do not attack application-type files
            if not "content-type" in resp_headers:
                # Sometimes there's no content-type... so we rely on the document extension
                if (page.split(".")[-1] not in self.allowed) and page[-1] != "/":
                    return
            elif not "text" in resp_headers["content-type"]:
                return

            err = ""
            payload = self.HTTP.quote(payload)
            url = page + "?" + payload
            if url not in self.attackedGET:
                self.attackedGET.append(url)
                evil_req = HTTP.HTTPResource(url)

                if self.verbose == 2:
                    print "+", url
                try:
                    resp = self.HTTP.send(evil_req, headers=headers)
                    data, code = resp.getPageCode()
                except requests.exceptions.Timeout, timeout:
                    # No timeout report here... launch blind sql detection later
                    data = ""
                    code = "408"
                    err = ""
                    resp = timeout
                else:
                    err = self.__findPatternInResponse(data)
                if err != "":
                    vuln_found += 1
                    self.logVuln(category=Vulnerability.SQL_INJECTION,
                                 level=Vulnerability.HIGH_LEVEL_VULNERABILITY,
                                 request=evil_req,
                                 info=err + " " + _("(QUERY_STRING)"))
                    print err, _("(QUERY_STRING) in"), page
                    print "  " + _("Evil url") + ":", evil_req.url

                    self.vulnerableGET.append(page + "?" + "__SQL__")

                else:
                    if code == "500":
                        self.logVuln(category=Vulnerability.SQL_INJECTION,
                                     level=Vulnerability.HIGH_LEVEL_VULNERABILITY,
                                     request=evil_req,
                                     info=VulDescrip.ERROR_500 + "\n" + VulDescrip.ERROR_500_DESCRIPTION)
                        print _("500 HTTP Error code with")
                        print "  " + _("Evil url") + ":", evil_req.url
        else:
            for i in range(len(params_list)):
                err = ""
                param_name = self.HTTP.quote(params_list[i][0])
                saved_value = params_list[i][1]
                params_list[i][1] = "__SQL__"
                pattern_url = page + "?" + self.HTTP.encode(params_list)
                if pattern_url not in self.attackedGET:
                    self.attackedGET.append(pattern_url)

                    params_list[i][1] = self.HTTP.quote(payload)
                    url = page + "?" + self.HTTP.encode(params_list)
                    evil_req = HTTP.HTTPResource(url)

                    if self.verbose == 2:
                        print "+", evil_req.url
                    try:
                        resp = self.HTTP.send(evil_req, headers=headers)
                        data, code = resp.getPageCode()
                    except requests.exceptions.Timeout, timeout:
                        # No timeout report here... launch blind sql detection later
                        data = ""
                        code = "408"
                        err = ""
                        resp = timeout
                    else:
                        err = self.__findPatternInResponse(data)
                    if err != "":
                        self.logVuln(category=Vulnerability.SQL_INJECTION,
                                     level=Vulnerability.HIGH_LEVEL_VULNERABILITY,
                                     request=evil_req,
                                     parameter=param_name,
                                     info=err + " (" + param_name + ")")
                        if self.color == 0:
                            print err, "(" + param_name + ") " + _("in"), page
                            print "  " + _("Evil url") + ":", evil_req.url
                        else:
                            print err, ":", evil_req.url.replace(param_name + "=", self.RED + param_name + self.STD + "=")
                        self.vulnerableGET.append(pattern_url)

                    elif code == "500":
                            self.logVuln(category=Vulnerability.SQL_INJECTION,
                                         level=Vulnerability.HIGH_LEVEL_VULNERABILITY,
                                         request=evil_req,
                                         parameter=param_name,
                                         info=VulDescrip.ERROR_500 + "\n" + VulDescrip.ERROR_500_DESCRIPTION)
                            print _("500 HTTP Error code with")
                            print "  " + _("Evil url") + ":", evil_req.url
                params_list[i][1] = saved_value

    def attackPOST(self, form):
        """This method performs the SQL Injection attack with method POST"""
        payload = "\xbf'\"("
        err = ""

        # copies
        get_params = form.get_params
        post_params = form.post_params
        file_params = form.file_params
        referer = form.referer

        for param_list in [get_params, post_params, file_params]:
            for i in xrange(len(param_list)):
                saved_value = param_list[i][1]

                param_list[i][1] = "__SQL__"
                param_name = self.HTTP.quote(param_list[i][0])
                attack_pattern = HTTP.HTTPResource(form.path,
                                                   method=form.method,
                                                   get_params=get_params,
                                                   post_params=post_params,
                                                   file_params=file_params)
                if attack_pattern not in self.attackedPOST:
                    self.attackedPOST.append(attack_pattern)

                    param_list[i][1] = payload
                    evil_req = HTTP.HTTPResource(form.path,
                                                 method=form.method,
                                                 get_params=get_params,
                                                 post_params=post_params,
                                                 file_params=file_params,
                                                 referer=referer)
                    if self.verbose == 2:
                        print "+", evil_req

                    try:
                        resp = self.HTTP.send(evil_req)
                        data, code = resp.getPageCode()
                    except requests.exceptions.Timeout, timeout:
                        # No timeout report here... launch blind sql detection later
                        data = ""
                        code = "408"
                        resp = timeout
                    else:
                        err = self.__findPatternInResponse(data)
                    if err != "":
                        self.logVuln(category=Vulnerability.SQL_INJECTION,
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
                        self.vulnerablePOST.append(attack_pattern)

                    else:
                        if code == "500":
                            self.logVuln(category=Vulnerability.SQL_INJECTION,
                                         level=Vulnerability.HIGH_LEVEL_VULNERABILITY,
                                         request=evil_req,
                                         parameter=param_name,
                                         info=_("500 HTTP Error code coming from") + " " + \
                                              referer + "\n" + VulDescrip.ERROR_500_DESCRIPTION)
                            print _("500 HTTP Error code in"), evil_req.url
                            print "  " + _("with params") + " =", self.HTTP.encode(post_params)
                            print "  " + _("coming from"), referer

                param_list[i][1] = saved_value
