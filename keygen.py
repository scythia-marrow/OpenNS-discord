from runner import readIni

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

if __name__ == "__main__":
	ini = readIni(open("openNS-discord.ini","r"))
	private_key = rsa.generate_private_key(
		public_exponent=65537,
		key_size=2048
		)
	public_key = private_key.public_key()
	pemprv = private_key.private_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PrivateFormat.PKCS8,
		encryption_algorithm=serialization.NoEncryption()
		)
	pempub = public_key.public_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PublicFormat.SubjectPublicKeyInfo,
		)
	prvfile = open(ini.cryptokey,"wb")
	pubfile = open(ini.cryptokey+".pub","wb")
	for line in pemprv.splitlines():
		prvfile.write(line+b'\n')
	for line in pempub.splitlines():
		pubfile.write(line+b'\n')
	prvfile.close()
	pubfile.close()
