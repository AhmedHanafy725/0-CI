from jumpscale.core.base import Base, fields, StoredFactory


class Document(Base):
    @property
    def id(self):
        return self.instance_name.strip("model")

    @property
    def name(self):
        return self.instance_name


class ModelFactory:
    _model = None

    @classmethod
    def get(cls, id):
        name = "model" + str(id)
        return cls._model.find(name)

    @classmethod
    def get_by_name(cls, name):
        return cls._model.find(name)

    @classmethod
    def list_all(cls):
        return cls._model.list_all()

    @classmethod
    def distinct(cls, field, **kwargs):
        if kwargs:
            objects = cls._model.find_many(**kwargs)
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
            objects = cls._model.find_many(**kwargs)
        else:
            objects = []
            objects_names = cls._model.list_all()
            for name in objects_names:
                objects.append(cls._model.find(name))

        if order_by:
            objects.sort(key=lambda x: getattr(x, order_by), reverse=not asc)

        results = []
        for obj in objects:
            obj_dict = {}
            for field in fields:
                obj_dict[field] = getattr(obj, field)
            obj_dict["id"] = obj.instance_name.strip("model")
            results.append(obj_dict)
        return results
