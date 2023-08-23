# Ash DAL
The library provides a standardized way to connect to DB, and Base DAO class implementation

## Installation

### PyPi

```shell
pip install ash-dal

# OR

poetry add ash-dal
```

### From github
In order to install Ash DAL directly from GitHub repository, run:
```shell
pip install git+https://github.com/meetash/ash-dal.git@main

# OR

poetry add git+https://github.com/meetash/ash-dal.git@main
```
## Usage
### Database class
There are two options: sync or async database connection.
#### Synchronous database
```python
from ash_dal import Database, URL
from ash_dal.utils import prepare_ssl_context
from models import User


ssl_context = prepare_ssl_context(
    ssl_root_dir='/tmp/certs',
    client_cert_path='client-cert.pem',
    client_key_path='client-key.pem',
    server_ca_path='server-ca.pem'
)

db_url = URL.create(
    drivername="mysql+pymysql",
    username="my_db_user",
    password="S3cret",
    host="127.0.0.1",
    port=3306,
    database="my_db",
)

read_replica_db_url = URL.create(
    drivername="mysql+pymysql",
    username="my_db_user",
    password="S3cret",
    host="127.0.0.1",
    port=3307,
    database="my_db",
)


DATABASE = Database(
	db_url=db_url,
	read_replica_url=read_replica_db_url,
	ssl_context=ssl_context,
    read_replica_ssl_context=ssl_context
)


def get_users(db: Database):
	with db.session as session:
		users = session.scalars(User)
	return users

```
#### Asynchronous database
```python
from ash_dal import AsyncDatabase, URL
from ash_dal.utils import prepare_ssl_context
from models import User


ssl_context = prepare_ssl_context(
    ssl_root_dir='/tmp/certs',
    client_cert_path='client-cert.pem',
    client_key_path='client-key.pem',
    server_ca_path='server-ca.pem'
)

db_url = URL.create(
    drivername="mysql+aiomysql",
    username="my_db_user",
    password="S3cret",
    host="127.0.0.1",
    port=3306,
    database="my_db",
)

read_replica_db_url = URL.create(
    drivername="mysql+aiomysql",
    username="my_db_user",
    password="S3cret",
    host="127.0.0.1",
    port=3307,
    database="my_db",
)


DATABASE = AsyncDatabase(
	db_url=db_url,
	read_replica_url=read_replica_db_url,
	ssl_context=ssl_context,
    read_replica_ssl_context=ssl_context
)

async def async_get_users(db: AsyncDatabase):
	async with db.session as session:
		users = await session.scalars(User)
	return users

```

### DAO Base class
Like you can use sync/async Database classes, there are also two variations of DAO Base class

#### Synchronous DAO Base class

```python

from dataclasses import dataclass

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from ash_dal import BaseDAO, Database, URL


class Base(DeclarativeBase):
    pass


class ExampleORMModel(Base):
    __tablename__ = "example_table"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[str] = mapped_column(String(64))
    age: Mapped[int]


@dataclass()
class ExampleEntity:
    id: int
    first_name: str
    last_name: str
    age: int


class ExampleDAO(BaseDAO[ExampleEntity]):
    __entity__ = ExampleEntity
    __model__ = ExampleORMModel


if __name__ == '__main__':
    db = Database(
        db_url=URL.create(
            drivername="mysql+pymysql",
            username="my_db_user",
            password="S3cret",
            host="127.0.0.1",
            port=3306,
            database="my_db",
        )
    )
    dao = ExampleDAO(database=db)

    entity = dao.get_by_pk(pk='some-primary-key')
```

#### Asynchronous DAO Base class

```python

from dataclasses import dataclass

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from ash_dal import AsyncBaseDAO, AsyncDatabase, URL
import asyncio


class Base(DeclarativeBase):
    pass


class ExampleORMModel(Base):
    __tablename__ = "example_table"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[str] = mapped_column(String(64))
    age: Mapped[int]


@dataclass()
class ExampleEntity:
    id: int
    first_name: str
    last_name: str
    age: int


class ExampleDAO(AsyncBaseDAO[ExampleEntity]):
    __entity__ = ExampleEntity
    __model__ = ExampleORMModel


if __name__ == '__main__':
    db = AsyncDatabase(
        db_url=URL.create(
            drivername="mysql+aiomysql",
            username="my_db_user",
            password="S3cret",
            host="127.0.0.1",
            port=3306,
            database="my_db",
        )
    )
    dao = ExampleDAO(database=db)
    entity = asyncio.run(dao.get_by_pk(pk='some-primary-key'))
```

### BaseDAO methods
The main goal of BaseDAO class is to provide CRUD methods that could be useful while building a basic CRUD API. 
`BaseDAO` class provides the following default methods:
#### Data fetching methods
- `BaseDAO.get_by_pk(pk)` - Using this method you can fetch an entity by its primary key.
    ```python
    entity = dao.get_by_pk(pk='AWABCD1234')
    ```
- `BaseDAO.all` - Using this method you can fetch all entities from the database. It's might be useful for fetching
    data from small tables where you don't actually need pagination (configs etc)
    ```python
    entities = dao.get_all()
    ```
- `BaseDAO.get_page(page_index, [page_size])` - Fetch a page with entities by page index. If the index is out of range, 
    an empty page will be returned. If `page_size` is not passed - the default page size (20) will be applied.
    ```python
    page = dao.get_page(page_index=2, page_size=10)
    for entity in page:
        # Do some stuff with entity
        ...
    ```
- `BaseDAO.paginate([specification, page_size])` - An iterator that returns pages with entities. A specification
    can be applied to fetch filtered data.
    ```python
    for page in dao.paginate(specification={'status': 'notified'}, page_size=15):
        # Do some stuff with page
        ...
    ```
- `BaseDAO.filter(specification)` - Fetch entities from database by specification. It's might be useful for fetching
    filtered data from small tables where you don't actually need pagination (configs etc)
    ```python
    entities = dao.filter(specification={'labId': 2})
    ```
#### Data manipulation methods
- `BaseDAO.create(data)` - Create an entity in database based on passed data. Returns back an entity
    ```python
    data = {'foo': 'bar'}
    entity = dao.create(data=data)
    ```
- `BaseDAO.bulk_create(data)` - Create multiple entities within one query. Unlike the previous method 
    this one doesn't return anything.
    ```python
    data = [{'foo': 'bar'}, {'foo': 'beer'}]
    dao.bulk_create(data=data)
    ```
- `BaseDAO.update(specification, update_data)` - Patch entity(ies) by specification.
    ```python
    update_data = {'foo': 'bar'}
    is_updated = dao.update(specification={'foo': 'beer'}, update_data=update_data)
    ```
- `BaseDAO.delete(specification)` - Remove entity(ies) by specification.
    ```python
    is_removed = dao.delete(specification={'id': 'some-id'},)
    ```

## Pagination strategies

By default the BaseDAO class uses the simplest pagination strategy that is based on SQL offset & limit mechanisms.
The library provides one more strategy out of the box that is called deferred join pagination. 
You can learn more about it [here](https://planetscale.com/learn/courses/mysql-for-developers/examples/deferred-joins). 

If you want to change the pagination strategy for you DAO class, you can do it by re-defining 
the `__paginator_factory__` field inside your DAO class:
```python
from ash_dal import BaseDAO, DeferredJoinPaginator
from ash_dal.utils import DeferredJoinPaginatorFactory, AsyncDeferredJoinPaginator

class ExampleEntity:
    ...

class ExampleORMModel:
    id: int
    ...

class ExampleDAO(BaseDAO[ExampleEntity]):
    __entity__ = ExampleEntity
    __model__ = ExampleORMModel
    __paginator_factory__ = DeferredJoinPaginatorFactory(
        paginator_class=DeferredJoinPaginator,
        pk_field=ExampleORMModel.id,
    )

# OR async

class ExampleAsyncDAO(BaseDAO[ExampleEntity]):
    __entity__ = ExampleEntity
    __model__ = ExampleORMModel
    __paginator_factory__ = DeferredJoinPaginatorFactory(
        paginator_class=AsyncDeferredJoinPaginator,
        pk_field=ExampleORMModel.id,
    )
```
### Custom pagination strategy
You can also define your own pagination strategy. Be aware that your paginator class should implement IPaginator or 
IAsyncPaginator interfaces:

```python
from ash_dal.utils.paginator.interface import IPaginator, IAsyncPaginator
from ash_dal import PaginatorPage
import typing as t

class ExampleORM:
    ...

class MyPaginator(IPaginator[ExampleORM]):
    def get_page(self, page_index: int) -> PaginatorPage[ExampleORM]:
        # Do page fetching
        ...

    def paginate(self) -> t.Iterator[PaginatorPage[ExampleORM]]:
        # Do pagination
        ...
    @property
    def size(self) -> int:
        # Get pages count
        return 10

# or async paginator

class MyAsyncPaginator(IAsyncPaginator[ExampleORM]):
    async def get_page(self, page_index: int) -> PaginatorPage[ExampleORM]:
        # Do page fetching asynchronously
        ...

    async def paginate(self) -> t.AsyncIterator[PaginatorPage[ExampleORM]]:
        # Do pagination asynchronously
        ...
    @property
    async def size(self) -> int:
        # Get pages count asynchronously
        return 10
```
