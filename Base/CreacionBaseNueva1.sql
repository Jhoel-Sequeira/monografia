CREATE DATABASE Vet_ElBuenProductor
go

USE Vet_ElBuenProductor
go

-- ************************************** [estado]
CREATE TABLE [estado]
(
 [id_estado]    int NOT NULL PRIMARY KEY IDENTITY,
 [NombreEstado] varchar(50) NOT NULL

);
GO
-- ************************************** [credenciales]
CREATE TABLE [credenciales] (
    id_credencial int PRIMARY KEY identity,
    usuario VARCHAR(max) NOT NULL,
    contrasena VARCHAR(max) NOT NULL,
	rol int not null,
	cargo int not null,

);
GO
-- ************************************** [cliente]
CREATE TABLE [cliente]
(
 [num_cliente]       int NOT NULL PRIMARY KEY  identity,
 [nombres_cliente]   varchar(max) NOT NULL ,
 [id_estado]         int NOT NULL ,
 [apellidos_cliente] varchar(max) NOT NULL ,
 [direccion_cliente] varchar(max) NOT NULL ,
 [correo_cliente]    varchar(max) NOT NULL ,
 [id_credencial]	int,

 FOREIGN KEY ([id_estado])  REFERENCES [estado]([id_estado]),
 FOREIGN KEY ([id_credencial])  REFERENCES [credenciales]([id_credencial])
);
GO

-- ************************************** [especie]
CREATE TABLE [especie]
(
 [id_especie]  int NOT NULL PRIMARY KEY identity,
 [nom_especie] nvarchar(max) NOT NULL ,
 [id_estado]   int NOT NULL ,

 FOREIGN KEY ([id_estado])  REFERENCES [estado]([id_estado])
);
GO
-- ************************************** [venta]
CREATE TABLE [venta]
(
 [cod_venta]   int NOT NULL PRIMARY KEY identity,
 [fecha_venta] datetime NOT NULL ,
 [num_cliente] int NOT NULL ,
 [total]       float NOT NULL ,

 FOREIGN KEY ([num_cliente])  REFERENCES [cliente]([num_cliente])
);
GO
-- ************************************** [proveedor]
CREATE TABLE [proveedor]
(
 [cod_proveedor]    int NOT NULL PRIMARY KEY identity,
 [nom_proveedor]    varchar(max) NOT NULL ,
 [id_estado]        int NOT NULL ,
 [info_proveedor]   varchar(max) NULL ,
 [dir_proveedor]    varchar(max) NOT NULL ,
 [correo_proveedor] varchar(max) NOT NULL ,

 FOREIGN KEY ([id_estado])  REFERENCES [estado]([id_estado])
);
GO
-- ************************************** [producto]
CREATE TABLE [producto]
(
 [cod_producto]  int NOT NULL PRIMARY KEY identity,
 [nom_producto]  varchar(max) NOT NULL ,
 [id_estado]     int NOT NULL ,
 [cod_proveedor] int NOT NULL ,
 [tipo_producto] int NOT NULL ,
 [precio]        float NOT NULL ,
 [stock_critico] int NOT NULL ,
 [stock]         int NOT NULL ,
 [unidad]        float NOT NULL ,

 FOREIGN KEY ([cod_proveedor])  REFERENCES [proveedor]([cod_proveedor]),
 FOREIGN KEY ([id_estado])  REFERENCES [estado]([id_estado])
);
GO
-- ************************************** [veterinario]
CREATE TABLE [veterinario]
(
 [num_veterinario] int NOT NULL PRIMARY KEY identity,
 [cod_veterinario] varchar(max) NOT NULL ,
 [id_estado]       int NOT NULL ,
 [nom_vet]         varchar(max) NOT NULL ,
 [dir_vet]         varchar(max) NOT NULL ,
 [cel_vet]         varchar(max) NOT NULL ,
 [correo_vet]      varchar(max) NOT NULL ,
 [id_credencial]	int,

 FOREIGN KEY ([id_estado])  REFERENCES [estado]([id_estado]),
 FOREIGN KEY ([id_credencial])  REFERENCES [credenciales]([id_credencial])
);
GO
-- ************************************** [Det_venta]
CREATE TABLE [Det_venta]
(
 [cod_producto_1] int NOT NULL PRIMARY KEY identity,
 [cod_venta_1]    int NOT NULL ,
 [cantidad]       int NOT NULL ,
 [precio_venta]   float NOT NULL ,

 FOREIGN KEY ([cod_venta_1])  REFERENCES [venta]([cod_venta]),
 FOREIGN KEY ([cod_producto_1])  REFERENCES [producto]([cod_producto])
);
GO
-- ************************************** [raza]
CREATE TABLE [raza]
(
 [id_raza]     int NOT NULL PRIMARY KEY identity,
 [nombre_raza] varchar(max) NOT NULL ,
 [id_estado]   int NOT NULL ,
 [id_especie]  int NOT NULL ,

 FOREIGN KEY ([id_estado])  REFERENCES [estado]([id_estado]),
 FOREIGN KEY ([id_especie])  REFERENCES [especie]([id_especie])
);
GO
-- ************************************** [mascota]
CREATE TABLE [mascota]
(
 [idMascota]         int NOT NULL PRIMARY KEY identity,
 [Nombre_mascota]    nvarchar(max) NOT NULL ,
 [id_estado]         int NOT NULL ,
 [id_raza]           int NOT NULL ,
 [num_cliente]       int NOT NULL ,
 [fecha_nac_mascota] datetime NOT NULL ,
 [sexo]              varchar(max) NOT NULL ,
 [color]             varchar(max) NOT NULL ,
 [fecha_ingreso]     datetime NOT NULL ,

 FOREIGN KEY ([id_estado])  REFERENCES [estado]([id_estado]),
 FOREIGN KEY ([num_cliente])  REFERENCES [cliente]([num_cliente]),
 FOREIGN KEY ([id_raza])  REFERENCES [raza]([id_raza])
);
GO
-- ************************************** [Atencion]
CREATE TABLE [atencion]
(
 [cod_atencion]    int NOT NULL PRIMARY KEY identity,
 [fecha_atencion]  datetime NOT NULL ,
 [num_cliente]     int NOT NULL ,
 [id_estado]       int NOT NULL ,
 [num_veterinario] int NOT NULL ,
 [idMascota]       int NOT NULL ,
 [tipo_atencion]   int NOT NULL ,
 [peso]            float NOT NULL ,
 [altura]          float NOT NULL ,
 [temperatura]     float NOT NULL ,
 [descripcion]     nvarchar(max) NOT NULL ,
 [costo]           float NOT NULL ,

 FOREIGN KEY ([id_estado])  REFERENCES [estado]([id_estado]),
 FOREIGN KEY ([num_cliente])  REFERENCES [cliente]([num_cliente]),
 FOREIGN KEY ([idMascota])  REFERENCES [mascota]([idMascota]),
 FOREIGN KEY ([num_veterinario])  REFERENCES [veterinario]([num_veterinario])
);
GO
-- ************************************** [hospitalizacion]
CREATE TABLE [hospitalizacion]
(
 [id_hosp]        int NOT NULL PRIMARY KEY identity,
 [fecha_hosp]     datetime NOT NULL ,
 [id_estado]      int NOT NULL ,
 [idMascota]      int NOT NULL ,
 [fecha_salida]   datetime NOT NULL ,
 [descripcion]    varchar(max) NOT NULL ,
 [total]          float NOT NULL ,
 [valor_consulta] float NOT NULL ,


 FOREIGN KEY ([idMascota])  REFERENCES [mascota]([idMascota]),
 FOREIGN KEY ([id_estado])  REFERENCES [estado]([id_estado])
);
GO

-- ************************************** [vacuna_mascota]
CREATE TABLE [vacuna_mascota]
(
 [num_vacuna]        int NOT NULL PRIMARY KEY identity,
 [dosis]             int NOT NULL ,
 [num_cliente]       int NOT NULL ,
 [cod_producto]      int NOT NULL ,
 [idMascota]         int NOT NULL ,
 [fecha_vacuna]      datetime NOT NULL ,
 [fecha_prox_vacuna] datetime NOT NULL ,

 FOREIGN KEY ([idMascota])  REFERENCES [mascota]([idMascota]),
 FOREIGN KEY ([cod_producto])  REFERENCES [producto]([cod_producto]),
 FOREIGN KEY ([num_cliente])  REFERENCES [cliente]([num_cliente])
);
GO
-- ************************************** [atencion_producto]
CREATE TABLE [atencion_producto]
(
 [cod_atencion] int NOT NULL PRIMARY KEY identity,
 [cod_producto] int NOT NULL ,
 [cantidad]     int NOT NULL ,
 [precio]       float NOT NULL ,

 FOREIGN KEY ([cod_producto])  REFERENCES [producto]([cod_producto]),
 FOREIGN KEY ([cod_atencion])  REFERENCES [atencion]([cod_atencion])
);
GO
-- ************************************** [hosp_producto]
CREATE TABLE [hosp_producto]
(
 [id_hosp]      int NOT NULL PRIMARY KEY identity,
 [cod_producto] int NOT NULL ,
 [periodo]      int NOT NULL ,
 [cantidad]     float NOT NULL ,
 [precio]       float NOT NULL ,


 FOREIGN KEY ([cod_producto])  REFERENCES [producto]([cod_producto]),
 FOREIGN KEY ([id_hosp])  REFERENCES [hospitalizacion]([id_hosp])
);
GO
-- ************************************** [Atencion costo]
CREATE TABLE [atencion_costo]
(
 [id_costo]     int NOT NULL PRIMARY KEY identity,
 [descripcion]  nvarchar(max) NOT NULL ,
 [cod_atencion] int NOT NULL ,
 [costo]        float NOT NULL ,

 FOREIGN KEY ([cod_atencion])  REFERENCES [atencion]([cod_atencion])
);
GO
-- ************************************** [ajuste_inventario]
CREATE TABLE [ajuste_inventario]
(
 [num_ajuste] int not null PRIMARY KEY identity,
 [fecha_hora]   datetime NOT NULL,
 [tipo_ajuste]  int NOT NULL ,
 [cod_producto] int NOT NULL ,
 [cantidad]     float NOT NULL ,

 FOREIGN KEY ([cod_producto])  REFERENCES [producto]([cod_producto])
);
GO
-- ************************************** [observacion]
CREATE TABLE [observacion]
(
 [num_observacion]   int NOT NULL PRIMARY KEY identity,
 [fecha_observacion] datetime NOT NULL ,
 [cod_atencion]      int NOT NULL ,
 [descripcion]       nvarchar(50) NOT NULL ,

 FOREIGN KEY ([cod_atencion])  REFERENCES [atencion]([cod_atencion])
);
GO
-- ************************************** [stock]
CREATE TABLE [stock]
(
 [cod_producto]    int NOT NULL PRIMARY KEY identity,
 [frascos]         int NOT NULL ,
 [cantidad_total]  float NOT NULL ,
 [cantidad_actual] float NOT NULL ,

 FOREIGN KEY ([cod_producto])  REFERENCES [producto]([cod_producto])
);
GO
-- ************************************** [Credenciales]

