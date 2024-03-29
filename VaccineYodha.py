import requests
from datetime import date,datetime
import os
import smtplib
from pygame import mixer 
from time import time,ctime
import yaml
from email.message import EmailMessage


class vaccineSpotter:
	def __init__(self, config_file_path, time_delay=1):
		self.config_file_path = config_file_path
		self.time_delay = time_delay
		self.cfg = self.read_config()
		self.set_params()

	def read_config(self):
		with open(self.config_file_path, "r") as ymlfile:
			cfg = yaml.safe_load(ymlfile)
		return cfg
		
	def set_params(self):

		self.email_info = self.cfg["email"]
		self.area_info = self.cfg["area_info"]

		self.sent_from = self.email_info['sent_from']
		self.email_user = self.sent_from
		self.email_password = self.email_info['email_password']

		self.to = self.email_info['to']

		self.__district_code = self.area_info['__district_code']
		self.__pincode = self.area_info['__pincode']

		self.age_limit_info = self.cfg['age_limit']
		self.age_limit = self.age_limit_info['age_limit']

	def send_email(self, result):
	
		msg = EmailMessage()
		body = "\n\n \t\tFollowing vaccines centers are found \n Query Time : \
				 "+ctime(time())+"\n\n" + result
		msg.set_content("\n\n \t\tFollowing vaccines centers are found \n Query Time : " +ctime(time())+"\n\n" + result)
		msg['Subject'] = 'Vaccine slot available in your area'
		msg['From'] = "MR.Virus Vaccine Detector ahuja" + self.sent_from
		msg['To'] = self.to
		email_text = """\ 
	%s
	""" % ( body)
		print(email_text)
		try:
			server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
			server.login(self.email_user, self.email_password)
			server.send_message(msg)
			server.quit()
			print('Your Email Has been sent MR.Virus!\n')
		except Exception as e:
			print('Error In Sending Email MR.Virus...')
			print (e)

	def parse_json_district_code(self, result):
		output = []
		centers = result['centers']
		for center in centers:
			sessions = center['sessions']
			for session in sessions:
				if session['available_capacity'] > 0:
					res = { 'name': center['name'], 'block_name':center['block_name'],\
					'age_limit':session['min_age_limit'], 'vaccine_type':session['vaccine'] ,\
					 'date':session['date'],'available_capacity':session['available_capacity'] }
					if res['age_limit'] in self.age_limit:
						output.append(res)
		return output


	def parse_json_pincode(self, result):
		output = []
		sessions = result['sessions']
		if len(sessions)==0:
			return output
		for session in sessions:
			if session['available_capacity'] >= 0:
				res = { 'name': session['name'], 'block_name':session['block_name'], \
				'age_limit':session['min_age_limit'], 'vaccine_type':session['vaccine'] , \
				'date':session['date'],'available_capacity':session['available_capacity'] }
				if res['age_limit'] in self.age_limit:
					output.append(res)
		return output

	def call_api(self, url, headers, query_type):
		response = requests.get(url, headers = headers)
		if response.status_code == 200:
			print("API call success")
			result = response.json()
			if query_type=='district_code':
				output = self.parse_json_district_code(result)
			elif query_type =='pincode':
				output = self.parse_json_pincode(result)
			else:
				print('incorrect query type\nquery type must be either district_code or pincode\n')
				return
			if len(output) > 0:
				print("Vaccines available")
				print('\007')
				result_str = ""
				for center in output:
					result_str = result_str + center['name'] + "\n"
					result_str = result_str + "block:"+center['block_name'] + "\n"
					result_str = result_str + "vaccine count:"+str(center['available_capacity']) + "\n"
					result_str = result_str + "vaccine type:"+ center['vaccine_type'] + "\n"
					result_str = result_str + center['date'] + "\n"
					result_str = result_str + "age_limit:"+str(center['age_limit'])+"\n"
					result_str = result_str + "-----------------------------------------------------\n"
				self.send_email(result_str)
				mixer.init()
				mixer.music.load('dingdong.wav')
				mixer.music.play()

			else:
				print("Vaccines not available for age limit {}\nTrying again\
				 after {} minute.....\n".format(*self.age_limit, self.time_delay))
		else:
			print("something went wrong :(\nStatus code {} \nTrying again......\
				after {} minute.....\n".format(response.status_code, self.time_delay))


	def query(self, root_url, headers, query_type):
		print(ctime(time()))
		
		today = date.today()
		d1 = today.strftime("%d/%m/%Y")
		__date = str(d1).replace("/","-")


		if query_type == 'district_code':
			url = root_url + "/calendarByDistrict?district_id=" + self.__district_code + "&date="+ __date

		elif query_type =='pincode':
			url = root_url + "/findByPin?pincode=" + self.__pincode + "&date=" + __date
		else:
			print('incorrect query type\nquery type must be either district_code or pincode\n')
			return
		self.call_api(url,  headers, query_type)


t = datetime.now()
if __name__ == '__main__':
	time_delay = 1
	#Change to pincode if you want to search by pincode
	query_type = 'district_code' 
	config_file_path = 'CONFIG.yml'
	
	print("querying by {} .....".format(query_type))
	root_url = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public"
	headers = {'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"}

	vaccineSpotter = vaccineSpotter(config_file_path, time_delay)
	vaccineSpotter.query(root_url, headers, query_type)

	while True:
		delta = datetime.now()-t
		if delta.seconds >= time_delay * 60:
			vaccineSpotter.query(root_url, headers, query_type)
			t = datetime.now()
