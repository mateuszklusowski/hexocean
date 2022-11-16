# Set up project
#### First, clone the project.
```bash
git clone https://github.com/mateuszklusowski/hexocean.git
```
#### Go to the project directory
```bash
cd hexocean
```
#### Install dependencies, then run project
```bash
docker-compose up
```
#### While project is running, load datas
```bash
docker-compose run --rm app sh -c " python manage.py loaddata fixtures.json"
```
#### Create superuser
```bash
docker-compose run --rm app sh -c " python manage.py createsuperuser"
```
#### Finnaly, log in to the admin panel to be authenticaded and assign a tier to the user
```bash
127.0.0.1:8000/admin
```
# Endpoints

&nbsp;
&nbsp;

## Get user's images
#### Enterprise tier version
![List](https://i.imgur.com/YBcmzy4.png)

&nbsp;
&nbsp;

## Upload image
![Upload](https://i.imgur.com/civ7ren.png)

&nbsp;
&nbsp;

## Create binary image link
```http
POST /api/images/{image_id}/create/
```
#### Before:
&nbsp;
![Before](https://i.imgur.com/ciiAldJ.png)
&nbsp;
#### After
&nbsp;
![After](https://i.imgur.com/byevofd.png)

&nbsp;
&nbsp;

## Get binary image link
&nbsp;
```http
GET /api/images/{binary_image_link_id}/
```
![Retrieve](https://i.imgur.com/cIdOfVm.png)