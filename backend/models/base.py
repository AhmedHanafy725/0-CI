from jumpscale.core.base import Base


class Document(Base):
    @property
    def run_id(self):
        return self.instance_name

    @property
    def name(self):
        return self.instance_name


class ModelFactory:
    _model = None

    @classmethod
    def get(cls, run_id):
        return cls._model.find(run_id)

    @classmethod
    def list_all(cls):
        return cls._model.list_all()

    @classmethod
    def delete(cls, name):
        cls._model.delete(name)

    @classmethod
    def distinct(cls, field, **kwargs):
        if kwargs:
            _, _, objects = cls._model.find_many(**kwargs)
        else:
            objects = []
            objects_names = cls._model.list_all()
            for name in objects_names:
                objects.append(cls._model.find(name))

        distinct_list = []
        for obj in objects:
            value = getattr(obj, field)
            if value not in distinct_list:
                distinct_list.append(value)

        return list(set(distinct_list))

    @classmethod
    def get_objects(cls, fields, order_by=None, asc=True, **kwargs):
        if kwargs:
            _, _, objects = cls._model.find_many(**kwargs)
        else:
            objects = []
            objects_names = cls._model.list_all()
            for name in objects_names:
                objects.append(cls._model.find(name))

        if order_by and order_by not in fields:
            fields.append(order_by)

        results = []
        for obj in objects:
            obj_dict = {}
            for field in fields:
                obj_dict[field] = getattr(obj, field)
            obj_dict["run_id"] = obj.instance_name
            results.append(obj_dict)

        if order_by:
            results.sort(key=lambda x: x[order_by], reverse=not asc)
        return results
