use movie;

select * from users;

ALTER TABLE movie MODIFY poster_url VARCHAR(10000);

select * from movie;



ALTER TABLE tickets 
ADD COLUMN base_cost DECIMAL(10,2) AFTER cost,
ADD COLUMN gst_amount DECIMAL(10,2) AFTER base_cost,
ADD COLUMN convenience_fee DECIMAL(10,2) AFTER gst_amount,
ADD COLUMN payment_method VARCHAR(20) AFTER convenience_fee;

show tables;