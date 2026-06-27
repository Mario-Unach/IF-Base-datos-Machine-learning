-- ====================================================================
-- 1. CREACIÓN DE TABLAS DE DIMENSIÓN (CATÁLOGOS)
-- ====================================================================
-- Creacion de la BDD
CREATE DATABASE CC_Client
GO

USE CC_Client
GO
-- Tabla para el género (Columna SEX)
CREATE TABLE dim_sexo (
    id_sexo INT PRIMARY KEY,
    descripcion_sexo VARCHAR(20) NOT NULL
);

-- Tabla para el nivel educativo (Columna EDUCATION)
CREATE TABLE dim_educacion (
    id_educacion INT PRIMARY KEY,
    nivel_educativo VARCHAR(50) NOT NULL
);

-- Tabla para el estado civil (Columna MARRIAGE)
CREATE TABLE dim_estado_civil (
    id_estado_civil INT PRIMARY KEY,
    descripcion_estado_civil VARCHAR(30) NOT NULL
);

-- Tabla para estandarizar los 6 meses de historial de la tarjeta
CREATE TABLE dim_tiempo_mes (
    id_mes INT PRIMARY KEY,
    mes_referencia VARCHAR(50) NOT NULL,
    orden_historial INT NOT NULL
);

-- (NUEVO) Tabla para el estatus de pago (Columna PAY_0 a PAY_6)
-- Esto ayuda a entender qué significa el -1, 1, 2, etc.
CREATE TABLE dim_estatus_pago (
    id_estatus INT PRIMARY KEY,
    descripcion_estatus VARCHAR(100) NOT NULL
);

-- ====================================================================
-- 2. CREACIÓN DE LA DIMENSIÓN CENTRAL (PERFIL DEL CLIENTE)
-- ====================================================================

CREATE TABLE dim_cliente (
    id_cliente INT PRIMARY KEY, -- Columna ID
    id_sexo INT NOT NULL,
    id_educacion INT NOT NULL,
    id_estado_civil INT NOT NULL,
    edad TINYINT NOT NULL, 
    limite_credito DECIMAL(18,2) NOT NULL, -- LIMIT_BAL
    
    CONSTRAINT FK_Cliente_Sexo FOREIGN KEY (id_sexo) REFERENCES dim_sexo(id_sexo),
    CONSTRAINT FK_Cliente_Educacion FOREIGN KEY (id_educacion) REFERENCES dim_educacion(id_educacion),
    CONSTRAINT FK_Cliente_EstadoCivil FOREIGN KEY (id_estado_civil) REFERENCES dim_estado_civil(id_estado_civil)
);

-- ====================================================================
-- 3. CREACIÓN DE LAS TABLAS DE HECHOS (TRANSACCIONAL Y ML)
-- ====================================================================

CREATE TABLE historial_pagos (
    id_historial BIGINT IDENTITY(1,1) PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_mes INT NOT NULL,
    id_estatus_pago INT NOT NULL,          -- PAY_0 a PAY_6
    monto_estado_cuenta DECIMAL(18,2),     -- BILL_AMT1 a BILL_AMT6
    monto_pago_anterior DECIMAL(18,2),     -- PAY_AMT1 a PAY_AMT6
    
    CONSTRAINT FK_Historial_Cliente FOREIGN KEY (id_cliente) REFERENCES dim_cliente(id_cliente),
    CONSTRAINT FK_Historial_Mes FOREIGN KEY (id_mes) REFERENCES dim_tiempo_mes(id_mes),
    CONSTRAINT FK_Historial_Estatus FOREIGN KEY (id_estatus_pago) REFERENCES dim_estatus_pago(id_estatus)
);

CREATE TABLE riesgo_crediticio (
    id_cliente INT PRIMARY KEY,
    incumplimiento_proximo_mes BIT NOT NULL, -- Target: default payment next month (0 o 1)
    
    CONSTRAINT FK_Riesgo_Cliente FOREIGN KEY (id_cliente) REFERENCES dim_cliente(id_cliente)
);

-- ====================================================================
-- 4. POBLAR LOS CATÁLOGOS CON LOS DETALLES EXACTOS (INSERTS)
-- ====================================================================

-- Catálogo de Sexo
INSERT INTO dim_sexo (id_sexo, descripcion_sexo) VALUES 
(1, 'Masculino'), 
(2, 'Femenino');

-- Catálogo de Educación (Basado en el diccionario oficial)
INSERT INTO dim_educacion (id_educacion, nivel_educativo) VALUES 
(0, 'Sin Instruccion'),
(1, 'Posgrado'), 
(2, 'Universidad'), 
(3, 'Bachillerato'), 
(4, 'Otros'), 
(5, 'Desconocido'),
(6, 'Desconocido');

-- Catálogo de Estado Civil
INSERT INTO dim_estado_civil (id_estado_civil, descripcion_estado_civil) VALUES 
(0, 'Desconocido'),
(1, 'Casado'), 
(2, 'Soltero'), 
(3, 'Otros');

-- Catálogo de Meses (Reflejando el historial de facturación)
INSERT INTO dim_tiempo_mes (id_mes, mes_referencia, orden_historial) VALUES 
(1, 'Mes 1 (Septiembre, 2005)', 1),
(2, 'Mes 2 (Agosto, 2005)', 2),
(3, 'Mes 3 (Julio, 2005)', 3),
(4, 'Mes 4 (Junio, 2005)', 4),
(5, 'Mes 5 (Mayo, 2005)', 5),
(6, 'Mes 6 (Abril, 2005)', 6);

-- Catálogo de Estatus de Pago (Aclarando el historial de retrasos)
INSERT INTO dim_estatus_pago (id_estatus, descripcion_estatus) VALUES 
(-2, 'Sin consumo / Inactivo'),
(-1, 'Pago puntual (Duly)'),
(0, 'Pago mínimo realizado / Crédito revolvente'),
(1, 'Retraso de 1 mes'),
(2, 'Retraso de 2 meses'),
(3, 'Retraso de 3 meses'),
(4, 'Retraso de 4 meses'),
(5, 'Retraso de 5 meses'),
(6, 'Retraso de 6 meses'),
(7, 'Retraso de 7 meses'),
(8, 'Retraso de 8 meses'),
(9, 'Retraso de 9 meses o más');


----MIGRACION

-- Crear tabla de paso para recibir el CSV crudo
CREATE TABLE staging_credit_cards (
    ID INT,
    LIMIT_BAL DECIMAL(18,2),
    SEX INT,
    EDUCATION INT,
    MARRIAGE INT,
    AGE INT,
    PAY_0 INT, PAY_2 INT, PAY_3 INT, PAY_4 INT, PAY_5 INT, PAY_6 INT,
    BILL_AMT1 DECIMAL(18,2), BILL_AMT2 DECIMAL(18,2), BILL_AMT3 DECIMAL(18,2), 
    BILL_AMT4 DECIMAL(18,2), BILL_AMT5 DECIMAL(18,2), BILL_AMT6 DECIMAL(18,2),
    PAY_AMT1 DECIMAL(18,2), PAY_AMT2 DECIMAL(18,2), PAY_AMT3 DECIMAL(18,2), 
    PAY_AMT4 DECIMAL(18,2), PAY_AMT5 DECIMAL(18,2), PAY_AMT6 DECIMAL(18,2),
    default_payment_next_month BIT
);

-- Cargar los datos del archivo a la tabla staging
-- Asegúrate de cambiar la ruta por la ubicación real de tu archivo
BULK INSERT staging_credit_cards
FROM '/var/opt/mssql/temp/default of credit card clients.csv'
WITH (
    FIELDTERMINATOR = ',',  -- El separador de tu archivo
    ROWTERMINATOR = '0x0a',   -- Salto de línea
    FIRSTROW = 3           -- Empezamos en la fila 3 porque la 1 y 2 son los encabezados (X1, ID, etc.)
);

-- POBLAR DATOS A TABLAS DIM
-- Insertar a dim_cliente
INSERT INTO dim_cliente (id_cliente, id_sexo, id_educacion, id_estado_civil, edad, limite_credito)
SELECT ID, SEX, EDUCATION, MARRIAGE, AGE, LIMIT_BAL
FROM staging_credit_cards;

-- Insertar a riesgo_crediticio
INSERT INTO riesgo_crediticio (id_cliente, incumplimiento_proximo_mes)
SELECT ID, default_payment_next_month
FROM staging_credit_cards;

SELECT * FROM dim_cliente
SELECT * FROM riesgo_crediticio

-------------------CROSS APLY
-- Transformar columnas a filas y enviar a historial_pagos
INSERT INTO  historial_pagos (id_cliente, id_mes, id_estatus_pago, monto_estado_cuenta, monto_pago_anterior)
SELECT 
    s.ID,
    meses.id_mes,
    meses.estatus,
    meses.estado_cuenta,
    meses.pago_anterior
FROM staging_credit_cards s
CROSS APPLY (
    VALUES 
        (1, s.PAY_0, s.BILL_AMT1, s.PAY_AMT1),
        (2, s.PAY_2, s.BILL_AMT2, s.PAY_AMT2),
        (3, s.PAY_3, s.BILL_AMT3, s.PAY_AMT3),
        (4, s.PAY_4, s.BILL_AMT4, s.PAY_AMT4),
        (5, s.PAY_5, s.BILL_AMT5, s.PAY_AMT5),
        (6, s.PAY_6, s.BILL_AMT6, s.PAY_AMT6)
) AS meses(id_mes, estatus, estado_cuenta, pago_anterior);

SELECT COUNT (*) FROM historial_pagos

-- Ejecutar para validar la numero de registros exactos
SELECT 
    (SELECT COUNT(*) FROM dim_cliente) AS Total_Clientes,
    (SELECT COUNT(*) FROM riesgo_crediticio) AS Total_Target_Riesgo,
    (SELECT COUNT(*) FROM historial_pagos) AS Total_Registros_Historial,
    (SELECT COUNT(*) * 6 FROM dim_cliente) AS Total_Historial_Esperado;

--
-- Ejecutar para revisar los primeros 10 clientes con sus textos descriptivos
SELECT TOP 10
    c.id_cliente,
    s.descripcion_sexo,
    e.nivel_educativo,
    ec.descripcion_estado_civil,
    c.edad,
    c.limite_credito,
    r.incumplimiento_proximo_mes
FROM dim_cliente c
INNER JOIN dim_sexo s ON c.id_sexo = s.id_sexo
INNER JOIN dim_educacion e ON c.id_educacion = e.id_educacion
INNER JOIN dim_estado_civil ec ON c.id_estado_civil = ec.id_estado_civil
INNER JOIN riesgo_crediticio r ON c.id_cliente = r.id_cliente
ORDER BY c.id_cliente;

-----
-- Ejecutar para auditar el comportamiento financiero de un cliente específico (Ejemplo: ID 1)
SELECT 
    hp.id_cliente,
    tm.mes_referencia,
    ep.descripcion_estatus AS estado_de_pago,
    hp.monto_estado_cuenta,
    hp.monto_pago_anterior
FROM historial_pagos hp
INNER JOIN dim_tiempo_mes tm ON hp.id_mes = tm.id_mes
INNER JOIN dim_estatus_pago ep ON hp.id_estatus_pago = ep.id_estatus
WHERE hp.id_cliente = 52 -- Se puede modificar este número para auditar otros clientes al azar
ORDER BY tm.orden_historial;