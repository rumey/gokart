from ftplib import FTP
import os

class FTPClient(object):
    url = None
    user = None
    password = None
    pasv = None

    def __enter__(self):
        self.ftp = FTP(self.url,self.user,self.password)
        self.ftp.set_pasv(self.pasv)
        return self

    def __exit__(self,exc_type,exc_value,traceback):
        if self.ftp:
            self.ftp.quit()
            self.ftp = None

    def get(self,remotefile,localfile):
        with open(localfile,"wb") as f:
            def saveFile(data):
                f.write(data)
            self.ftp.retrbinary("RETR {}".format(remotefile),saveFile)
    

    def getMdtm(self,remotefile):
        response = self.ftp.sendcmd("Mdtm " + remotefile).split(None,1)
        if response[0] == "213":
            return response[1]
        else:
            raise Exception("{}:{}".format(*response))


class BomFTP(FTPClient):
    url = os.environ.get("BOM_FTP_URL")
    user = os.environ.get("BOM_FTP_USER")
    password = os.environ.get("BOM_FTP_PASSWORD")
    pasv = (os.environ.get("BOM_FTP_PASV") or "false").lower() in ("true","yes","t","y","on")

