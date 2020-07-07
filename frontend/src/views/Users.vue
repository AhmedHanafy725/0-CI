<template>
  <v-card>
    <v-data-table :headers="headers" :items="itemsWithIndex" class="elevation-1">
      <template v-slot:top>
        <v-toolbar flat color="white">
          <v-toolbar-title>Users</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-dialog v-model="dialog" max-width="500px">
            <template v-slot:activator="{ on, attrs }">
              <a
                v-bind="attrs"
                v-on="on"
                class="btn btn-label-info btn-bold btn-sm btn-icon-h kt-margin-l-10"
              >New User</a>
            </template>
            <v-card>
              <v-card-title>
                <span class="headline">{{ formTitle }}</span>
              </v-card-title>

              <v-card-text>
                <v-container>
                  <v-row>
                    <v-col cols="12" sm="6">
                      <v-text-field
                        v-model="editedUser.name"
                        label="Username"
                        placeholder="user.3bot"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12" sm="6">
                      <v-text-field
                        v-model="editedUser.role"
                        label="Role"
                        placeholder="admin / user"
                      ></v-text-field>
                    </v-col>
                  </v-row>
                </v-container>
              </v-card-text>

              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="blue darken-1" text @click="close">Cancel</v-btn>
                <v-btn color="blue darken-1" text @click="save">Save</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>
        </v-toolbar>
      </template>

      <!-- #ID -->
      <template v-slot:item.id="{ item }">
        <span>{{ item.id }}</span>
      </template>

      <!-- Username -->
      <template v-slot:item.name="{ item }">
        <span>{{ userName(item.name) }}</span>
      </template>

      <!-- Role -->
      <template v-slot:item.role="{ item }">
        <span
          class="kt-badge kt-badge--inline"
          :class="item.role == 'admin' ? 'kt-badge--info' : 'kt-badge--warning'"
        >{{ item.role }}</span>
      </template>

      <template v-slot:item.actions="{ item }">
        <v-icon small v-if="item.role !== 'admin'" class="mr-2" @click="editUser(item)">mdi-pencil</v-icon>
        <v-icon small @click="deleteUser(item)">mdi-delete</v-icon>
      </template>
    </v-data-table>
  </v-card>
</template>

<script>
import EventService from "../services/EventService";
export default {
  name: "Users",
  data: () => ({
    dialog: false,
    search: "",
    headers: [
      { text: "#", value: "id" },
      { text: "Name", value: "name" },
      { text: "Role", value: "role" },
      { text: "Actions", value: "actions", sortable: false }
    ],
    data: [],
    editedIndex: -1,
    editedUser: {
      name: "",
      role: ""
    },
    defaultItem: {
      id: "",
      name: "",
      role: ""
    }
  }),

  computed: {
    formTitle() {
      return this.editedIndex === -1 ? "New User" : "Edit User";
    },
    itemsWithIndex() {
      return this.data.map((items, id) => ({
        ...items,
        id: id + 1
      }));
    }
  },

  watch: {
    dialog(val) {
      val || this.close();
    }
  },

  created() {
    this.getUsers();
  },

  methods: {
    getUsers() {
      EventService.getUsers()
        .then(response => {
          this.loading = false;
          this.data = response.data;
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    userName(name) {
      return name.replace(".3bot", " ");
    },

    editUser(item) {
      this.editedIndex = this.data.indexOf(item);
      this.editedUser = Object.assign({}, item);
      this.dialog = true;
    },

    deleteUser(item) {
      this.editedUser = Object.assign({}, item);
      confirm("Are you sure you want to delete this User?");
      if (this.editedUser.role == "admin") {
        EventService.deleteUser({ admin: this.editedUser.name })
          .then(response => {
            toastr.success(response.data);
            this.getUsers();
          })
          .catch(error => {
            toastr.error(error.response.data);
            console.log("Error! Could not reach the API. " + error);
          });
      } else if (this.editedUser.role == "user") {
        EventService.deleteUser({ user: this.editedUser.name })
          .then(response => {
            toastr.success(response.data);
            this.getUsers();
          })
          .catch(error => {
            toastr.error(error.response.data);
            console.log("Error! Could not reach the API. " + error);
          });
      }
    },

    close() {
      this.dialog = false;
      this.$nextTick(() => {
        this.editedUser = Object.assign({}, this.defaultItem);
        this.editedIndex = -1;
      });
    },

    save() {
      if (this.editedUser.role == "admin") {
        EventService.addUser({ admin: this.editedUser.name })
          .then(response => {
            toastr.success(response.data);
            this.getUsers();
          })
          .catch(error => {
            toastr.error(error.response.data);
            console.log("Error! Could not reach the API. " + error);
          });
      } else if (this.editedUser.role == "user") {
        EventService.addUser({ user: this.editedUser.name })
          .then(response => {
            toastr.success(response.data);
            this.getUsers();
          })
          .catch(error => {
            toastr.error(error.response.data);
            console.log("Error! Could not reach the API. " + error);
          });
      }
      this.close();
    }
  }
};
</script>

<style scoped>
a.btn.btn-label-info {
  background-color: #5578eb;
  color: #fff;
}
</style>
