## website_rentals
This module allows you to publish products that can be rented on your webshop.<br/>

Sample:
![image](https://user-images.githubusercontent.com/6352350/158194953-c22d3903-388d-449c-807a-dbabeaffc020.png)


## Configuration
### Product configuration
All products that you want to rent out have to meet the following criteria:
- Be of the type "Stockable", as this is used to check if a product/service can be rented out or not,
- Have the option "Can be Rented" on, as this is used to define the check-out pop-up to choose dates and timeslots,
- Have rental pricing rules setup (under the "Rental" tab)

When these criteria are met the product is available in the webshop and can be rented out as soon as you publish the product.<br/>
The ability to choose another variant on a second rental pricing rule adds support for example variant prices in your rental.<br/>
A sample could be where you rent out a bike in black, red and blue and they all have different physical stock. <br/>
In this case Odoo will look at the available stock of that variant (e.g the red bike) and see if that is rentable.<br/>
This also means you could configure separate prices per variant, for example because your red bikes are super sexy and sell so well.

### Rental pricing rules & price computations
The pricing rules are built that way that it can support product variants along with separate prices for different times.<br/>
A sample here could be a meeting room which you'd like to offer at a different rate for booking it a whole day, four hours or a specific time. <br/>
For example let's look at this configuration:
![image](https://user-images.githubusercontent.com/6352350/158197081-fa55f5be-ce9c-49ee-861b-9a183b0aa25c.png)


In this case if a customer wants to book for 4 hours he/she pays 250€, if he she/books for 10 hours (so a full day) it costs 330€. <br/>
If the customer books any time in between the 4 and 10 hours we take the 4 hours slot at 250€ and then apply the price configured in the field "Extra hour" to compute a new price. <br/>
This means that if the customer books for 6 hours we'd do 250€ (4 hours) plus the extra hour price (80€) times the amount of hours over 4 (2 hours) which ends up with a price of 410€. <br/>
The lowest rule, which is defined in hours, is used as a basis and is only tried to fit in once. Anything over the first time (4 hours here) will add the extra hour price. <br/>
This means that if a customer would book for 8 hours we do <b>not</b> do 2x 250€ (because of the 4 hours block) but 1x 250€ + (4 hours times the extra hour price of 80€) ending up at 570€ in this sample.


### Time slot generation
The timeslots in the webshop are automatically computed and shown.<br/>
This is done based on the rental pricing rule (on the rental tab of the product) that is in the unit "Hours" and follows the duration set on the rule.<br/>
For example: if you have a rental pricing rule with a duration of 4 hours and the start time is 08:00 and the endtime is 18:00 there can only be two starting slots: 08:00 and 12:00.<br/>
The end slots are then computed in hour intervals. E.g for 4 hour intervals it mean they can start booking at either 08:00 or 12:00 but they can book until 12:00, 13:00, 14:00, 15:00, 16:00, 17:00 and 18:00.<br/>
The lower the unit is the more timeslots you'll get and the more combinations to rent out. For example on a rule of 2 hours you'd get the following possible start slots:
- 08:00
- 10:00
- 12:00
- 14:00
- 16:00

With the following possible end times:
- 10:00
- 11:00
- 12:00
- 13:00
- 14:00
- 15:00
- 16:00
- 17:00
- 18:00

### Date formats
When adding a rental product into your basket we store the booked dates in separate fields, in UTC, in the database.<br/>
The dates are stored as strings for showing in the basket and are formatted in the datetime format from your administrator user. <br/>
This means that you have to make sure that your administrator user has the right language set on the contact form, from which we will follow the date(time) format in the front-end. <br/> A sample for a database where the administrator user has the language German & the webshop is in German:
![image](https://user-images.githubusercontent.com/6352350/158199453-12ffdf0c-f028-4ffb-8140-b53b03af46a4.png)

