# moon服务器安装脚本

## 安装方法参考

### linux安装zerotier命令

curl -s <https://install.zerotier.com> | sudo bash

zerotier-cli join <your_network_id>

cd /var/lib/zerotier-one
zerotier-idtool initmooon identity.public >>moon.json
vi moon.json

修改行：
 "stableEndpoints": ["111.173.104.139/9993"] # 云服务器地址/9993端口

zerotier-idtool genmoon moon.json

mkdir /var/lib/zerotier-one/moons.d
cp 000000334bf08301.moon moons.d/

systemctl restart zerotier-one

加入moon
zerotier-cli orbit 334bf08301 334bf08301
zerotier-cli orbit 334bf08301

删除moon
cd /var/lib/zerotier-one/moons.d/
sudo rm 334bf08301.moon # 请确保这里的 ID 是您要删除的 Moon ID

### Planet服务器搭建

curl -O <https://s3-us-west-1.amazonaws.com/key-networks/deb/ztncui/1/x86_64/ztncui_0.8.14_amd64.deb>
dpkg -i ztncui_0.8.14_amd64.deb
sh -c "echo ZT_TOKEN=`sudo cat /var/lib/zerotier-one/authtoken.secret` > /opt/key-networks/ztncui/.env"
sh -c "echo HTTP_ALL_INTERFACES=yes >> /opt/key-networks/ztncui/.env"
sh -c "echo NODE_ENV=production >> /opt/key-networks/ztncui/.env"
chmod 400 /opt/key-networks/ztncui/.env
chown ztncui:ztncui /opt/key-networks/ztncui/.env
systemctl enable ztncui
systemctl restart ztncui

#### 创建完成信息

wrote 000000334bf08301.moon (signed world with timestamp 1748697036027)

## 要求

1.学习、参考以上安装方法，制作moon服务器安装脚本
2.脚本需要有交互式输入，支持用户输入免密登陆vps的ssh命令
3.脚本完成后将结果带日期时间戳保存到output目录
