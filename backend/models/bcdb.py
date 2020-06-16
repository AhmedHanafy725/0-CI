class Base:
    _model = None
    _model_obj = None

    def save(self):
        self._model_obj.save()

    def delete(self):
        self._model_obj.delete()

    @property
    def id(self):
        return self._model_obj.id

    @classmethod
    def distinct(cls, field, where=None):
        result = cls._model.query_model([f"distinct {field}"], whereclause=where).fetchall()
        distinct_list = []
        for i in result:
            for j in i:
                distinct_list.append(j)
        return distinct_list

    @classmethod
    def get_objects(cls, fields, where=None, order_by=None, asc=True):
        fields_string = ", ".join([f"[{x}]" for x in fields])
        query = f"select {fields_string}, [id] FROM {cls._model.index.sql_table_name}"
        if where:
            query += f" where {where}"
        if order_by:
            order = "asc" if asc else "desc"
            query += f" order by {order_by} {order}"
        query += ";"
        values = cls._model.query(query).fetchall()
        results = []
        for value in values:
            obj = {}
            for i, field in enumerate(fields):
                if field == "bin_release" and value[i] == "no":
                    obj[field] = None
                else:
                    obj[field] = value[i]
            obj["id"] = value[i + 1]
            results.append(obj)
        return results
