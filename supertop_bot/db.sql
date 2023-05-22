create table bot_user (
  telegram_id bigint primary key,
  created_at timestamp default current_timestamp not null
);

create table book_category (
  id integer primary key,
  created_at timestamp default current_timestamp not null,
  name varchar(60) not null unique,
  ordering integer not null unique
);

create table book (
  id integer primary key,
  created_at timestamp default current_timestamp not null,
  name text,
  category_id integer,
  ordering integer not null,
  read_start date,
  read_finish date,
  read_comments text,
  foreign key(category_id) references book_category(id),
  check (
    (
      read_finish > read_start
      and read_finish is not null
      and read_start is not null
    ) or (
      read_finish is null or read_start is null
    )
  ),
  unique(category_id, ordering)
);

create table voting (
  id integer primary key,
  voting_start date not null unique,
  voting_finish date not null unique,
  check (voting_finish > voting_start)
);

create table vote (
  vote_id integer,
  user_id bigint,
  first_book_id integer,
  second_book_id integer,
  third_book_id integer,
  foreign key(vote_id) references voting(id),
  foreign key(user_id) references bot_user(telegram_id),
  foreign key(first_book_id) references book(id),
  foreign key(second_book_id) references book(id),
  foreign key(third_book_id) references book(id),
  primary key(vote_id, user_id)
);

create table bot_user_in_vote_mode (
  user_id bigint
);

insert into book_category (name, ordering) values 
  ('Как писать хорошо, а нехорошо не писать', 10),

insert into book (name, category_id, ordering) values 
  ('Чистый код :: Роберт Мартин', 1, 1),
  

